# POVTales

What if stories were told from the perspective of the characters?

POVTales is a Streamlit app for chatting with story characters. It loads local story packages, uses each package as canon, and keeps the conversation aware of character point of view, story timeline, and spoiler settings.

The app does not fetch story text from the web at runtime. A story becomes available only when it has a local package under `stories/`.

## Current Features

- Dynamic story and character loading from local story packages
- Character profiles with voice, traits, and goals
- Story-moment selection and spoiler policy controls
- Timeline-aware character knowledge boundaries
- Retrieval over source text for full-story spoiler mode
- Reader-age guidance in the system prompt
- Deterministic evals for timeline and spoiler rules

## Project Roadmap

See [ROADMAP.md](ROADMAP.md) for the planned path toward multi-story support, timeline-aware roleplay, canon validation, evaluations, and an MCP server.

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
- Story moment
- Spoiler setting
- Reader age
- Model

Spoiler modes:

- `No spoilers`: the character only uses events they personally know at the selected moment.
- `Spoilers up to selected moment`: the answer may use canon up to the selected moment while separating story facts from personal character knowledge.
- `Full-story spoilers`: the answer may use the whole source story when asked.

## Run Evaluations

The deterministic evaluation suite checks timeline and spoiler boundaries without calling the OpenAI API:

```bash
.venv/bin/python evals/run_evals.py
```

Results are written to `evals/results/`.

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

The app discovers packages automatically as long as all four files exist. Timeline `known_by` values should use character ids; those events drive spoiler and point-of-view boundaries in the chat.

## Included Stories

### Fairy Tales

- [Beauty and the Beast](stories/beauty_and_the_beast/source.txt)
  - Beauty
  - Beast
  - Merchant
  - Fairy
- [Cinderella](stories/cinderella/source.txt)
  - Cinderella
  - Stepmother
  - Stepsister
  - Prince
- [Little Red Riding Hood](stories/little_red_riding_hood/source.txt)
  - Little Red Riding Hood
  - Wolf
  - Grandmother
  - Huntsman
- [Rapunzel](stories/rapunzel/source.txt)
  - Rapunzel
  - Enchantress
  - Prince
  - Rapunzel's Father
- [Rumpelstiltskin](stories/rumpelstiltskin/source.txt)
  - Miller's Daughter
  - Rumpelstiltskin
  - King
  - Messenger
- [Snow White](stories/snow_white/source.txt)
  - Snow White
  - Prince
  - Queen
  - Hunter
- [Sleeping Beauty](stories/sleeping_beauty/source.txt)
  - Rosamond (Sleeping Beauty)
  - Thirteenth Wise Woman
  - King
  - Prince

### Short Stories

- [The Cask of Amontillado](stories/the_cask_of_amontillado/source.txt)
  - Montresor
  - Fortunato
  - Luchresi
  - Montresor's Attendant
- [The Tell-Tale Heart](stories/the_tell_tale_heart/source.txt)
  - Narrator
  - Old Man
  - Police Officer
  - Neighbor
