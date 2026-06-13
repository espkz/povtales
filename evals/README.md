# POVTales Evaluations

The evaluation suite checks whether story timeline, source retrieval, and spoiler boundaries are being enforced before the app sends context to the model.

Run it from the project root:

```bash
python evals/run_evals.py
```

Or with the project virtual environment:

```bash
.venv/bin/python evals/run_evals.py
```

The runner reads `evals/cases.json` and writes JSON plus Markdown reports to `evals/results/`.

## Case Fields

- `story`: story title from the app selector.
- `character`: playable character name.
- `timeline_event_id`: selected story moment.
- `spoiler_mode`: one of `No spoilers`, `Spoilers up to selected moment`, or `Full-story spoilers`.
- `prompt`: representative user prompt for the scenario.
- `expected_known_event_ids`: events the character should personally know.
- `expected_allowed_event_ids`: events the response context may use as canon.
- `forbidden_known_event_ids`: events the character must not personally know.
- `forbidden_allowed_event_ids`: events the response context must not reveal.
- `expected_source_event_ids`: optional source-passage event tags that must be retrievable.
- `forbidden_source_event_ids`: optional source-passage event tags that must not be retrievable. If omitted, `forbidden_allowed_event_ids` is reused.

These evals do not call the OpenAI API. They are deterministic checks for the story engine's context and tagged-source retrieval rules. A later Phase 4 or Phase 5 pass can reuse the same cases to evaluate generated model responses for canon fidelity, voice, spoiler safety, and age appropriateness.
