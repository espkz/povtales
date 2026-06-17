import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_DIR))

from langchain_core.messages import HumanMessage, SystemMessage

from utils import (
    StoryChatbot,
    create_chat_model,
    extract_json_object,
    normalize_api_key,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CASES_PATH = BASE_DIR / "live_cases.json"
DEFAULT_RESULTS_DIR = BASE_DIR / "results"
DEFAULT_API_KEY_PATH = REPO_DIR / "api_key.txt"
DEFAULT_MODEL = "gpt-5-nano"
RUBRIC_DIMENSIONS = [
    "canon_fidelity",
    "character_voice",
    "conversational_fit",
    "grounded_imagination",
    "age_appropriateness",
    "retrieval_usefulness",
]


def main():
    parser = argparse.ArgumentParser(
        description="Run live POVTales model-response evaluations with gpt-5-nano."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Path to a live eval case JSON file.",
    )
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=DEFAULT_API_KEY_PATH,
        help="Path to a text file containing the OpenAI API key.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Directory where JSON and Markdown reports should be written.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model used for both generation and judging. Defaults to gpt-5-nano.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Optional limit for quick smoke runs.",
    )
    args = parser.parse_args()

    api_key = load_api_key(args.api_key_file)
    cases = load_cases(args.cases)
    if args.max_cases is not None:
        cases = cases[: args.max_cases]

    if args.model != DEFAULT_MODEL:
        raise SystemExit("Live evals are configured to use gpt-5-nano.")

    results = []
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']}", flush=True)
        results.append(evaluate_case(case, api_key, args.model))
    report = build_report(results, args.model)
    write_report(report, args.results_dir)

    print(
        f"{report['passed']}/{report['total']} live evals passed "
        f"({report['score']:.1%}) using {args.model}."
    )

    if report["failed"]:
        raise SystemExit(1)


def load_api_key(path):
    raw = os.environ.get("OPENAI_API_KEY", "")
    if not raw and path.exists():
        raw = path.read_text(encoding="utf-8")

    api_key = normalize_api_key(raw)
    if not api_key:
        raise SystemExit(
            f"No API key found. Put it in {path} or set OPENAI_API_KEY."
        )

    return api_key


def load_cases(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(case, api_key, model):
    chatbot = StoryChatbot(
        story=case["story"],
        role=case["character"],
        age=case.get("age", 10),
        model=model,
        response_mode=case.get("mode", "Chat"),
        api_key=api_key,
        validate_responses=False,
    )
    response = chatbot.respond(case["prompt"])
    judgment = judge_response(case, response, chatbot, api_key, model)
    dimension_scores = [
        int(judgment.get("scores", {}).get(dimension, 0))
        for dimension in RUBRIC_DIMENSIONS
    ]
    average_score = (
        sum(dimension_scores) / len(dimension_scores)
        if dimension_scores
        else 0
    )
    min_dimension_score = min(dimension_scores) if dimension_scores else 0
    passed = (
        average_score >= case.get("min_average_score", 4.0)
        and min_dimension_score >= case.get("min_dimension_score", 3)
    )

    return {
        "id": case["id"],
        "story": case["story"],
        "character": case["character"],
        "mode": case.get("mode", "Chat"),
        "prompt": case["prompt"],
        "response": response,
        "retrieved_sources": chatbot.last_sources,
        "judgment": judgment,
        "average_score": average_score,
        "min_dimension_score": min_dimension_score,
        "passed": passed,
    }


def judge_response(case, response, chatbot, api_key, model):
    judge = create_chat_model(model, api_key=api_key, temperature=0)
    result = judge.invoke(
        [
            SystemMessage(content=build_judge_system_prompt()),
            HumanMessage(
                content=build_judge_user_prompt(case, response, chatbot)
            ),
        ]
    )
    return parse_judgment(result.content)


def build_judge_system_prompt():
    return "\n".join(
        [
            "You are a strict evaluator for POVTales character responses.",
            "Score the response on each rubric dimension from 1 to 5.",
            "Use 5 for excellent, 3 for acceptable, and 1 for poor.",
            "Reward grounded imagination when it is clearly framed as possibility rather than canon.",
            "Penalize canon contradictions, generic assistant voice, book-report phrasing, ignored user intent, unsafe age tone, and unsupported claims.",
            "Return JSON only with this shape:",
            '{"scores": {"canon_fidelity": 5, "character_voice": 5, "conversational_fit": 5, "grounded_imagination": 5, "age_appropriateness": 5, "retrieval_usefulness": 5}, "strengths": ["..."], "issues": ["..."], "summary": "..."}',
        ]
    )


def build_judge_user_prompt(case, response, chatbot):
    return "\n\n".join(
        [
            f"Story: {case['story']}",
            f"Character: {case['character']}",
            f"Mode: {case.get('mode', 'Chat')}",
            f"Reader age: {case.get('age', 10)}",
            "Case criteria:\n" + format_list(case.get("criteria", [])),
            "Story context:\n" + chatbot.get_story_context(),
            "Retrieved source context:\n" + (chatbot.last_context or "None."),
            "User prompt:\n" + case["prompt"],
            "Candidate response:\n" + response,
        ]
    )


def format_list(items):
    if not items:
        return "- None."
    return "\n".join(f"- {item}" for item in items)


def parse_judgment(raw_content):
    try:
        data = json.loads(extract_json_object(raw_content))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return {
            "scores": {dimension: 0 for dimension in RUBRIC_DIMENSIONS},
            "strengths": [],
            "issues": [f"Judge did not return parseable JSON: {exc}"],
            "summary": raw_content,
        }

    scores = data.get("scores", {})
    normalized_scores = {}
    for dimension in RUBRIC_DIMENSIONS:
        normalized_scores[dimension] = clamp_score(scores.get(dimension, 0))

    return {
        "scores": normalized_scores,
        "strengths": ensure_string_list(data.get("strengths", [])),
        "issues": ensure_string_list(data.get("issues", [])),
        "summary": str(data.get("summary", "")),
    }


def clamp_score(value):
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = 0
    return max(0, min(5, score))


def ensure_string_list(value):
    if not isinstance(value, list):
        return [str(value)]
    return [str(item) for item in value]


def build_report(results, model):
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    failed = total - passed
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "type": "live",
        "model": model,
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
    json_path = results_dir / f"{stamp}.live.json"
    markdown_path = results_dir / "latest_live.md"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    with (results_dir / "latest_live.json").open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")

    markdown_path.write_text(format_markdown_report(report), encoding="utf-8")


def format_markdown_report(report):
    lines = [
        "# POVTales Live Evaluation Results",
        "",
        f"- Timestamp: `{report['timestamp']}`",
        f"- Model: `{report['model']}`",
        f"- Score: `{report['passed']}/{report['total']}` ({report['score']:.1%})",
        "",
        "| Case | Status | Avg | Min | Issues |",
        "| --- | --- | --- | --- | --- |",
    ]

    for result in report["results"]:
        status = "pass" if result["passed"] else "fail"
        issues = "; ".join(result["judgment"].get("issues", []))
        lines.append(
            f"| `{result['id']}` | {status} | "
            f"{result['average_score']:.2f} | "
            f"{result['min_dimension_score']} | {issues} |"
        )

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
