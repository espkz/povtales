# POVTales

What if stories were told from the perspective of the characters?

POVTales is a Streamlit app for chatting with story characters. It loads local story packages, uses each package as canon, and keeps the conversation aware of character point of view, story timeline, and reader age.

The app does not fetch story text from the web at runtime. A story becomes available only when it has a local package under `stories/`.

## Current Features

- Dynamic story and character loading from local story packages
- Character profiles with voice, traits, and goals
- Full-story retrieval over timeline-tagged source passages
- Timeline-aware character context
- Optional canon, POV, and tone validation with one revision pass
- Reader-age guidance in the system prompt
- Deterministic evals for story packages, timeline knowledge, and source tags

## Project Roadmap

See [ROADMAP.md](ROADMAP.md) for the planned path toward multi-story support, timeline-aware roleplay, canon validation, evaluations, and an MCP server.

For a deeper explanation of the engine, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Enter your OpenAI API key in the sidebar when the app opens. Then choose:

- Story
- Character
- Reader age
- Model

Advanced debug controls are available in the sidebar expander:

- Whether to validate responses
- Whether to show grounding details

The app uses the full local source story as canon, so characters can discuss the whole story when asked.

## Manual Smoke Test

After starting Streamlit, try:

- `Snow White` / `Queen`: ask what happened in the forest. With defaults, she can discuss the full story.
- `The Cask of Amontillado` / `Fortunato`: ask why Montresor is taking him to the vaults. He can answer with the full story canon available.
- Toggle `Show grounding details` to inspect the retrieved source passages and validation result.

`Validate responses` can add up to two extra model calls per answer: one validation call, and one revision call only if validation fails.

## Run Evaluations

The deterministic evaluation suite checks story package wiring, timeline knowledge, and source passage tags without calling the OpenAI API:

```bash
.venv/bin/python evals/run_evals.py
```

Results are written to `evals/results/`.

## Validation

When `Validate responses` is enabled, POVTales asks the model to review each draft response against the story timeline, source passages, character point of view, and reader age. If the validator finds an issue, the app asks for one revised response before displaying it.

Use `Show grounding details` to inspect the retrieved source context and validation result for each answer.

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

The app discovers packages automatically as long as all four files exist. Timeline `known_by` values should use character ids; those events give the chatbot character-specific context while retrieval can use the full local source story.

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
