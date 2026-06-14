# POVTales Evaluations

The evaluation suite checks whether story packages, timeline knowledge, and source passage tags are wired correctly before the app sends context to the model.

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
- `timeline_event_id`: timeline moment used to check character knowledge.
- `prompt`: representative user prompt for the scenario.
- `expected_known_event_ids`: events the character should personally know.
- `forbidden_known_event_ids`: events the character must not personally know.
- `expected_source_event_ids`: source-passage event tags that must be present.
- `forbidden_source_event_ids`: optional source-passage event tags that must not be present.

These evals do not call the OpenAI API. They are deterministic checks for the story engine's local data and tagged-source retrieval inputs. A later Phase 4 or Phase 5 pass can reuse the same cases to evaluate generated model responses for canon fidelity, voice, and age appropriateness.
