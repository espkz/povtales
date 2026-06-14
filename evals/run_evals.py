import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_DIR))

from story_data import (
    STORY_PACKAGES,
    get_character_profile,
    get_events_known_by,
    get_timeline_event,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CASES_PATH = BASE_DIR / "cases.json"
DEFAULT_RESULTS_DIR = BASE_DIR / "results"


def main():
    parser = argparse.ArgumentParser(
        description="Run deterministic POVTales story package evaluations."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Path to an evaluation case JSON file.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Directory where JSON and Markdown reports should be written.",
    )
    args = parser.parse_args()

    cases = load_cases(args.cases)
    results = [evaluate_case(case) for case in cases]
    report = build_report(results)
    write_report(report, args.results_dir)

    print(
        f"{report['passed']}/{report['total']} evals passed "
        f"({report['score']:.1%})."
    )

    if report["failed"]:
        raise SystemExit(1)


def load_cases(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(case):
    story = STORY_PACKAGES[case["story"]]
    character = get_character_profile(story, case["character"])
    get_timeline_event(story, case["timeline_event_id"])

    actual_known_event_ids = [
        event.id
        for event in get_events_known_by(
            story,
            character.id,
            case["timeline_event_id"],
        )
    ]
    actual_source_event_ids = sorted(
        {
            passage.event_id
            for passage in story.passages
        }
    )

    checks = [
        check_required(
            "known",
            actual_known_event_ids,
            case.get("expected_known_event_ids", []),
        ),
        check_forbidden(
            "known",
            actual_known_event_ids,
            case.get("forbidden_known_event_ids", []),
        ),
        check_required(
            "source",
            actual_source_event_ids,
            case.get("expected_source_event_ids", []),
        ),
        check_forbidden(
            "source",
            actual_source_event_ids,
            case.get("forbidden_source_event_ids", []),
        ),
    ]
    failures = [failure for check in checks for failure in check]

    return {
        "id": case["id"],
        "story": case["story"],
        "character": case["character"],
        "timeline_event_id": case["timeline_event_id"],
        "prompt": case["prompt"],
        "passed": not failures,
        "failures": failures,
        "actual_known_event_ids": actual_known_event_ids,
        "actual_source_event_ids": actual_source_event_ids,
    }


def check_required(section, actual_event_ids, expected_event_ids):
    missing = [
        event_id
        for event_id in expected_event_ids
        if event_id not in actual_event_ids
    ]
    return [
        f"{section} events missing expected event: {event_id}"
        for event_id in missing
    ]


def check_forbidden(section, actual_event_ids, forbidden_event_ids):
    present = [
        event_id
        for event_id in forbidden_event_ids
        if event_id in actual_event_ids
    ]
    return [
        f"{section} events included forbidden event: {event_id}"
        for event_id in present
    ]


def build_report(results):
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    failed = total - passed
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "timestamp": timestamp,
        "total": total,
        "passed": passed,
        "failed": failed,
        "score": passed / total if total else 0,
        "results": results,
    }


def write_report(report, results_dir):
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = report["timestamp"].replace(":", "-")
    json_path = results_dir / f"{stamp}.json"
    markdown_path = results_dir / "latest.md"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    with (results_dir / "latest.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    markdown_path.write_text(format_markdown_report(report), encoding="utf-8")


def format_markdown_report(report):
    lines = [
        "# POVTales Evaluation Results",
        "",
        f"- Timestamp: `{report['timestamp']}`",
        f"- Score: `{report['passed']}/{report['total']}` ({report['score']:.1%})",
        "",
        "| Case | Status | Notes |",
        "| --- | --- | --- |",
    ]

    for result in report["results"]:
        status = "pass" if result["passed"] else "fail"
        notes = "; ".join(result["failures"]) if result["failures"] else ""
        lines.append(f"| `{result['id']}` | {status} | {notes} |")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
