import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
DEFAULT_CASES_PATH = BASE_DIR / "quality_cases.json"
DEFAULT_RESULTS_DIR = BASE_DIR / "results"

BOOK_REPORT_PHRASES = [
    "in this tale",
    "the story says",
    "the story doesn't say",
    "the story does not say",
    "the book says",
    "the book does not say",
    "there isn't any example",
]
GENERIC_ASSISTANT_PHRASES = [
    "as an ai",
    "as a language model",
    "i cannot roleplay",
]
FIRST_PERSON_RE = re.compile(r"\b(i|i'm|i’d|i'll|i’ve|me|my|mine|we|we're|our)\b", re.I)


def main():
    parser = argparse.ArgumentParser(
        description="Run deterministic POVTales transcript quality evaluations."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Path to a quality case JSON file.",
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
        f"{report['passed']}/{report['total']} quality evals passed "
        f"({report['score']:.1%})."
    )

    if report["failed"]:
        raise SystemExit(1)


def load_cases(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(case):
    transcript_path = resolve_case_path(case["transcript_path"])
    turns = parse_transcript(transcript_path.read_text(encoding="utf-8"))
    checks = []

    checks.extend(check_transcript_shape(turns))
    checks.extend(check_forbidden_phrases(turns, case.get("forbidden_phrases", [])))
    checks.extend(check_forbidden_phrases(turns, GENERIC_ASSISTANT_PHRASES))
    checks.extend(
        check_book_report_language(
            turns,
            max_count=case.get("max_book_report_phrases", 0),
        )
    )
    checks.extend(
        check_first_person_voice(
            turns,
            min_ratio=case.get("min_first_person_turn_ratio", 0.6),
        )
    )
    checks.extend(check_turn_rules(turns, case.get("turn_checks", [])))

    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks else 1
    min_score = case.get("min_score", 0.8)
    failures = [check["message"] for check in checks if not check["passed"]]

    return {
        "id": case["id"],
        "story": case.get("story", ""),
        "character": case.get("character", ""),
        "mode": case.get("mode", ""),
        "transcript_path": str(transcript_path.relative_to(REPO_DIR)),
        "passed": score >= min_score,
        "score": score,
        "min_score": min_score,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "failures": failures,
        "checks": checks,
    }


def resolve_case_path(path):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return REPO_DIR / candidate


def parse_transcript(raw_text):
    blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n", raw_text)
        if block.strip()
    ]
    turns = []
    for index, block in enumerate(blocks):
        role = "user" if index % 2 == 0 else "assistant"
        turns.append({"role": role, "content": block})
    return turns


def assistant_turns(turns):
    return [turn for turn in turns if turn["role"] == "assistant"]


def check_transcript_shape(turns):
    checks = [
        {
            "name": "has_turns",
            "passed": bool(turns),
            "message": "" if turns else "transcript has no turns",
        },
        {
            "name": "starts_with_user",
            "passed": bool(turns) and turns[0]["role"] == "user",
            "message": (
                ""
                if bool(turns) and turns[0]["role"] == "user"
                else "transcript does not start with a user turn"
            ),
        },
    ]
    if turns:
        alternating = all(
            turn["role"] == ("user" if index % 2 == 0 else "assistant")
            for index, turn in enumerate(turns)
        )
        checks.append(
            {
                "name": "alternating_roles",
                "passed": alternating,
                "message": "" if alternating else "transcript roles do not alternate user/assistant",
            }
        )
    return checks


def check_forbidden_phrases(turns, forbidden_phrases):
    checks = []
    assistant_text = "\n".join(turn["content"] for turn in assistant_turns(turns)).lower()
    for phrase in forbidden_phrases:
        phrase_lower = phrase.lower()
        passed = phrase_lower not in assistant_text
        checks.append(
            {
                "name": f"forbidden_phrase:{phrase}",
                "passed": passed,
                "message": "" if passed else f"assistant used forbidden phrase: {phrase}",
            }
        )
    return checks


def check_book_report_language(turns, max_count):
    assistant_text = "\n".join(turn["content"] for turn in assistant_turns(turns)).lower()
    matches = [
        phrase
        for phrase in BOOK_REPORT_PHRASES
        if phrase in assistant_text
    ]
    return [
        {
            "name": "book_report_language",
            "passed": len(matches) <= max_count,
            "message": (
                ""
                if len(matches) <= max_count
                else "assistant sounded like a book report: " + ", ".join(matches)
            ),
        }
    ]


def check_first_person_voice(turns, min_ratio):
    responses = assistant_turns(turns)
    if not responses:
        return [
            {
                "name": "first_person_voice",
                "passed": False,
                "message": "no assistant turns to evaluate for first-person voice",
            }
        ]

    first_person_count = sum(
        1
        for response in responses
        if FIRST_PERSON_RE.search(response["content"])
    )
    ratio = first_person_count / len(responses)
    return [
        {
            "name": "first_person_voice",
            "passed": ratio >= min_ratio,
            "message": (
                ""
                if ratio >= min_ratio
                else (
                    f"first-person voice ratio {ratio:.0%} is below required "
                    f"{min_ratio:.0%}"
                )
            ),
        }
    ]


def check_turn_rules(turns, turn_checks):
    checks = []
    for rule in turn_checks:
        user_index = find_user_turn(turns, rule["user_contains"])
        if user_index is None or user_index + 1 >= len(turns):
            checks.append(
                {
                    "name": f"turn_found:{rule['user_contains']}",
                    "passed": False,
                    "message": f"could not find assistant response for user turn: {rule['user_contains']}",
                }
            )
            continue

        response = turns[user_index + 1]["content"]
        response_lower = response.lower()
        checks.append(
            {
                "name": f"turn_found:{rule['user_contains']}",
                "passed": True,
                "message": "",
            }
        )

        include_any = rule.get("assistant_should_include_any", [])
        if include_any:
            passed = any(item.lower() in response_lower for item in include_any)
            checks.append(
                {
                    "name": f"assistant_should_include_any:{rule['user_contains']}",
                    "passed": passed,
                    "message": (
                        ""
                        if passed
                        else (
                            f"assistant response to '{rule['user_contains']}' did not include any of: "
                            + ", ".join(include_any)
                        )
                    ),
                }
            )

        for forbidden in rule.get("assistant_should_not_include", []):
            passed = forbidden.lower() not in response_lower
            checks.append(
                {
                    "name": f"assistant_should_not_include:{forbidden}",
                    "passed": passed,
                    "message": (
                        ""
                        if passed
                        else (
                            f"assistant response to '{rule['user_contains']}' included forbidden text: "
                            f"{forbidden}"
                        )
                    ),
                }
            )
    return checks


def find_user_turn(turns, needle):
    needle_lower = needle.lower()
    for index, turn in enumerate(turns):
        if turn["role"] == "user" and needle_lower in turn["content"].lower():
            return index
    return None


def build_report(results):
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    failed = total - passed
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "type": "quality",
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
    json_path = results_dir / f"{stamp}.quality.json"
    markdown_path = results_dir / "latest_quality.md"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    with (results_dir / "latest_quality.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    markdown_path.write_text(format_markdown_report(report), encoding="utf-8")


def format_markdown_report(report):
    lines = [
        "# POVTales Quality Evaluation Results",
        "",
        f"- Timestamp: `{report['timestamp']}`",
        f"- Score: `{report['passed']}/{report['total']}` ({report['score']:.1%})",
        "",
        "| Case | Status | Check Score | Notes |",
        "| --- | --- | --- | --- |",
    ]

    for result in report["results"]:
        status = "pass" if result["passed"] else "fail"
        notes = "; ".join(result["failures"])
        check_score = f"{result['passed_checks']}/{result['total_checks']}"
        lines.append(f"| `{result['id']}` | {status} | {check_score} | {notes} |")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
