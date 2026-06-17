# POVTales Evaluations

POVTales has three evaluation layers:

- Data evals check story packages, timeline knowledge, and source passage tags before any model response is generated.
- Quality evals check saved transcripts with deterministic conversation-quality rules.
- Live evals generate model responses and use a model judge to score them against rubrics.

The data and quality suites run locally without an API key. Live evals call the OpenAI API.

## Quick Commands

Run data evals:

```bash
.venv/bin/python evals/run_evals.py
```

Run saved-chat quality evals:

```bash
.venv/bin/python evals/run_quality_evals.py
```

Run the full local suite:

```bash
.venv/bin/python evals/run_comprehensive_evals.py --allow-quality-failures
```

Run live model-response evals:

```bash
.venv/bin/python evals/run_live_evals.py
```

Live evals read an API key from `api_key.txt` first, then from `OPENAI_API_KEY`. `api_key.txt` is ignored by git.

Results are written as JSON and Markdown reports under `evals/results/`, which is also ignored by git.

## Data Evals

Data evals are defined in `evals/cases.json`. They test whether the app builds the right context for a story, character, and timeline moment.

Case fields:

- `story`: story title from the app selector.
- `character`: playable character name.
- `timeline_event_id`: story moment used to check character knowledge.
- `prompt`: representative user prompt for the scenario.
- `expected_known_event_ids`: events the selected character should personally know.
- `forbidden_known_event_ids`: events the selected character must not personally know.
- `expected_source_event_ids`: source-passage event tags that should be retrievable.
- `forbidden_source_event_ids`: optional source-passage event tags that must not be present.

These evals are useful when editing `stories/*/timeline.json`, adding a story package, or changing retrieval/context assembly.

## Quality Evals

Quality evals are defined in `evals/quality_cases.json` and inspect saved transcripts under `evals/chats/`.

Case fields:

- `transcript_path`: saved transcript file to inspect.
- `story`, `character`, `mode`: scenario metadata.
- `min_score`: minimum check ratio required to pass.
- `forbidden_phrases`: text that should not appear in assistant turns.
- `turn_checks`: targeted checks for an assistant response after a matching user turn.

Quality evals do not prove a conversation is excellent. They are regression checks for patterns the project has already seen, such as book-report phrasing, weak what-if answers, generic assistant behavior, and voice/canon mistakes.

## Live Evals

Live evals are defined in `evals/live_cases.json`. They run the actual `StoryChatbot`, then ask a model judge to score the answer.

Case fields:

- `story`, `character`, `mode`, `age`: app setup used to create the response.
- `prompt`: user prompt sent to `StoryChatbot`.
- `criteria`: scenario-specific expectations for the judge.
- `min_average_score`: minimum average rubric score required to pass.
- `min_dimension_score`: minimum allowed score for any rubric dimension.

Live evals use `gpt-5-nano` for both generation and judging. The judge scores:

- canon fidelity
- character voice
- conversational fit
- grounded imagination
- age appropriateness
- retrieval usefulness

Use live evals before larger behavior changes, prompt rewrites, or release-like commits. They cost API calls, so the local suites are better for frequent iteration.

## Reading Results

Each runner writes timestamped files plus latest aliases:

```text
evals/results/
  latest.json
  latest.md
  latest_quality.json
  latest_quality.md
  latest_comprehensive.json
  latest_comprehensive.md
  latest_live.json
  latest_live.md
```

The Markdown reports are intended for quick reading. The JSON reports are better for comparing exact scores or debugging failed cases.
