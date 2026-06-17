import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import run_evals
import run_quality_evals


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = BASE_DIR / "results"


def main():
    parser = argparse.ArgumentParser(
        description="Run all local POVTales deterministic and transcript-quality evaluations."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Directory where JSON and Markdown reports should be written.",
    )
    parser.add_argument(
        "--allow-quality-failures",
        action="store_true",
        help="Write the comprehensive report but exit 0 even if quality transcript evals fail.",
    )
    args = parser.parse_args()

    data_cases = run_evals.load_cases(run_evals.DEFAULT_CASES_PATH)
    data_results = [run_evals.evaluate_case(case) for case in data_cases]
    data_report = run_evals.build_report(data_results)

    quality_cases = run_quality_evals.load_cases(run_quality_evals.DEFAULT_CASES_PATH)
    quality_results = [
        run_quality_evals.evaluate_case(case)
        for case in quality_cases
    ]
    quality_report = run_quality_evals.build_report(quality_results)

    report = build_report(data_report, quality_report)
    write_report(report, args.results_dir)

    print(
        "Comprehensive evals: "
        f"data {data_report['passed']}/{data_report['total']} passed; "
        f"quality {quality_report['passed']}/{quality_report['total']} passed."
    )

    if report["failed"] and not args.allow_quality_failures:
        raise SystemExit(1)


def build_report(data_report, quality_report):
    timestamp = datetime.now(timezone.utc).isoformat()
    failed = data_report["failed"] + quality_report["failed"]
    total = data_report["total"] + quality_report["total"]
    passed = data_report["passed"] + quality_report["passed"]

    return {
        "type": "comprehensive",
        "timestamp": timestamp,
        "total": total,
        "passed": passed,
        "failed": failed,
        "score": passed / total if total else 0,
        "data": data_report,
        "quality": quality_report,
    }


def write_report(report, results_dir):
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = report["timestamp"].replace(":", "-")
    json_path = results_dir / f"{stamp}.comprehensive.json"
    markdown_path = results_dir / "latest_comprehensive.md"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    with (results_dir / "latest_comprehensive.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    markdown_path.write_text(format_markdown_report(report), encoding="utf-8")


def format_markdown_report(report):
    lines = [
        "# POVTales Comprehensive Evaluation Results",
        "",
        f"- Timestamp: `{report['timestamp']}`",
        f"- Overall: `{report['passed']}/{report['total']}` ({report['score']:.1%})",
        f"- Data checks: `{report['data']['passed']}/{report['data']['total']}`",
        f"- Quality checks: `{report['quality']['passed']}/{report['quality']['total']}`",
        "",
        "## Quality Failures",
        "",
    ]

    failed_quality = [
        result
        for result in report["quality"]["results"]
        if not result["passed"]
    ]
    if not failed_quality:
        lines.append("None.")
    else:
        for result in failed_quality:
            lines.append(
                f"- `{result['id']}`: "
                f"{result['passed_checks']}/{result['total_checks']} checks passed."
            )
            for failure in result["failures"]:
                lines.append(f"  - {failure}")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.path.insert(0, str(BASE_DIR))
    main()
