# POVTales

POVTales is a Streamlit app for chatting with story characters.

It loads local story packages, uses each package as canon, and shapes responses around the selected character, story timeline, response mode, and reader age. The goal is not a generic character chatbot; it is a grounded reading companion that can answer questions, explore motivations, and play with "what if" ideas while staying anchored to the supplied text.

The app does not fetch story text from the web at runtime. A story is available only when it has a local package under `stories/`.

## Features

- Automatic story and character loading from local story packages
- Character profiles with voice, traits, goals, fears, and relationships
- Retrieval over timeline-tagged source passages
- Character knowledge context from timeline `known_by` data
- Response modes for chat, retelling, motivation, what-if questions, and scene continuation
- Reader-age guidance in the system prompt
- Optional response validation with one revision pass
- Optional grounding details for debugging retrieved context
- Local and live evaluation suites

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Provide an OpenAI API key in one of these places:

- Streamlit sidebar input
- `OPENAI_API_KEY` in your shell
- `.streamlit/secrets.toml`
- `.env`

Local secret files are ignored by git.

## Use The App

Choose a story, character, response mode, reader age, and model from the sidebar. The main chat then answers as the selected character.

Advanced controls live in a sidebar expander:

- `Validate responses`: asks the model to review the draft answer for canon, point of view, age, and tone issues. This can add one or two extra model calls.
- `Show grounding details`: displays retrieved source passages and validation details for debugging.

Good smoke-test prompts:

- `Snow White` / `Queen`: "What happened in the forest?"
- `The Cask of Amontillado` / `Fortunato` / `Explain Motivation`: "Why is Montresor taking you to the vaults?"
- `Rumpelstiltskin` / `Miller's Daughter` / `What If`: "What might have happened if you never had a child?"

## Story Packages

Each story lives in its own folder:

```text
stories/
  snow_white/
    source.txt
    metadata.json
    characters.json
    timeline.json
```

The app discovers packages automatically when all four files exist.

- `source.txt`: the story text used for retrieval and grounding.
- `metadata.json`: title, genre, source notes, and recommended age range.
- `characters.json`: playable characters, voice, traits, goals, fears, and relationships.
- `timeline.json`: ordered story events, character presence, character knowledge, and source passage tags.

Timeline `known_by` values should use character ids. These events give the chatbot character-specific context, while retrieval can still search the full local source.

## Included Stories

### Fairy Tales

| Story | Playable Characters |
| --- | --- |
| [Beauty and the Beast](stories/beauty_and_the_beast/source.txt) | Beauty, Beast, Merchant, Fairy |
| [Cinderella](stories/cinderella/source.txt) | Cinderella, Stepmother, Stepsister, Prince |
| [Little Red Riding Hood](stories/little_red_riding_hood/source.txt) | Little Red Riding Hood, Wolf, Grandmother, Huntsman |
| [Rapunzel](stories/rapunzel/source.txt) | Rapunzel, Enchantress, Prince, Rapunzel's Father |
| [Rumpelstiltskin](stories/rumpelstiltskin/source.txt) | Miller's Daughter, Rumpelstiltskin, King, Messenger |
| [Snow White](stories/snow_white/source.txt) | Snow White, Prince, Queen, Hunter |
| [Sleeping Beauty](stories/sleeping_beauty/source.txt) | Rosamond (Sleeping Beauty), Thirteenth Wise Woman, King, Prince |

### Short Stories

| Story | Playable Characters |
| --- | --- |
| [The Cask of Amontillado](stories/the_cask_of_amontillado/source.txt) | Montresor, Fortunato, Luchresi, Montresor's Attendant |
| [The Tell-Tale Heart](stories/the_tell_tale_heart/source.txt) | Narrator, Old Man, Police Officer, Neighbor |

## Evaluations

Data evals check story package wiring, timeline knowledge, and source passage tags without calling the OpenAI API:

```bash
.venv/bin/python evals/run_evals.py
```

Saved-chat quality evals check transcript behavior with deterministic rules:

```bash
.venv/bin/python evals/run_quality_evals.py
```

Run both local suites together:

```bash
.venv/bin/python evals/run_comprehensive_evals.py --allow-quality-failures
```

Live model-response evals use `gpt-5-nano` for generation and judging. Put an API key in ignored `api_key.txt` or set `OPENAI_API_KEY`, then run:

```bash
.venv/bin/python evals/run_live_evals.py
```

Reports are written to `evals/results/`, which is ignored by git. See [evals/README.md](evals/README.md) for case fields and runner details.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for completed phases and planned work on larger story worlds, richer story data, and agentic story exploration.
