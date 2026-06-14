# POVTales Roadmap

POVTales should grow from a single-story chatbot into a narrative AI engine: a system that can load different story worlds, speak from a character's point of view, and stay grounded in canon.

The long-term goal is not to clone a general character chatbot. The stronger angle is a canon-grounded storytelling system that can talk through a story from a chosen character's perspective.

## Product Direction

POVTales lets a reader choose:

- a story or world
- a character
- a reader age or tone

The character can then chat, retell events, explain motivations, or continue a scene from their own perspective while using the story source as grounding.

## Guiding Principles

- Keep the public demo focused on public-domain, open-licensed, or original stories.
- Design the architecture so it can handle larger fictional worlds later.
- Treat stories as structured data, not hardcoded app choices.
- Preserve character point of view: characters should sound like themselves and distinguish firsthand experience from broader story canon.
- Prefer small, verifiable upgrades over large rewrites.
- Add evaluation early so improvements can be measured.

## Phase 1: Stabilize The Current App

Goal: make the existing Snow White app clean, reliable, and easy to extend.

Tasks:

- Fix Streamlit state so changing story, character, age, or model resets the active chatbot.
- Move hardcoded story and character choices out of the UI.
- Use project-relative paths for story and prompt files.
- Strengthen the system prompt for point of view, canon, age appropriateness, and response length.
- Clean up dependencies and generated files.
- Update the README with local run instructions.

Status: complete for the current baseline.

## Phase 2: Story Packages

Goal: make adding a new story mostly a data task.

Create a package structure like:

```text
stories/
  snow_white/
    source.txt
    metadata.json
    characters.json
    timeline.json
```

`metadata.json` should describe the story:

```json
{
  "id": "snow_white",
  "title": "Snow White",
  "genre": "fairy tale",
  "source": "public domain",
  "recommended_age_min": 5,
  "recommended_age_max": 12
}
```

`characters.json` should describe playable characters:

```json
[
  {
    "id": "snow_white",
    "name": "Snow White",
    "role": "protagonist",
    "traits": ["kind", "gentle", "trusting"],
    "goals": ["stay safe", "find kindness"],
    "voice": "warm, gentle, hopeful"
  }
]
```

`timeline.json` should describe major events:

```json
[
  {
    "id": "queen_mirror_warning",
    "summary": "The mirror tells the Queen that Snow White is fairer.",
    "characters_present": ["queen"],
    "known_by": ["queen"]
  }
]
```

Implementation tasks:

- Replace the current flat `stories/snow_white.txt` setup with story folders.
- Add a loader that discovers available stories automatically.
- Populate the Streamlit story and character dropdowns from metadata.
- Keep backwards compatibility while migrating the existing Snow White story.

Status: complete for the current Snow White package.

## Phase 3: Character Point Of View

Goal: make the bot behave like a character with limited knowledge, not an omniscient narrator.

Tasks:

- Add character profiles with traits, voice, goals, fears, and relationships.
- Add character knowledge context based on timeline events. Done for current timeline `known_by` data.
- Use timeline-tagged source passages so retrieved context can be inspected and improved. Done.
- Keep the user-facing app focused on full-story character chat. Done.

Status: mostly complete. The app now has character profiles, timeline context, and retrieval over timeline-tagged source passages. The remaining Phase 3 polish is to enrich character profiles with fears and relationships.

Resume value:

> Built a point-of-view simulation layer that combines character profiles, timeline knowledge, and source-grounded retrieval.

## Phase 4: Canon Grounding And Validation

Goal: reduce contradictions and make the AI feel more trustworthy.

Tasks:

- Add a canon checker that reviews generated responses for contradictions. Done for a first LLM-based validation pass.
- Ask the model to revise when a response violates canon or character knowledge. Done with one revision pass.
- Show optional "story grounding" passages in the UI for debugging. Done.
- Track which retrieved passages influenced each answer. Partially done through displayed source context; structured per-answer citation tracking is still future work.
- Add response modes:
  - chat
  - retell scene
  - explain motivation
  - continue scene

Status: in progress. The app now validates draft responses for canon, point-of-view, age, and tone issues, then revises once when needed. Remaining Phase 4 work is richer source citation tracking and response modes.

Possible flow:

```text
user message
-> retrieve story context
-> generate character response
-> check canon and point of view
-> revise if needed
-> display final response
```

Resume value:

> Implemented retrieval-augmented generation with post-generation canon validation for character-based storytelling.

## Phase 5: Evaluations

Goal: prove the system is improving.

Create a small evaluation set with prompts like:

- "Queen, why did you send Snow White into the forest?"
- "Snow White, what did the mirror tell the Queen?"
- "Hunter, why did you spare Snow White?"
- "Tell me what happens after the poisoned apple."

Score responses for:

- canon fidelity
- character consistency
- age appropriateness
- retrieval relevance

Tasks:

- Add `evals/` with sample prompts and expected constraints. Done for deterministic story package and source-tag cases.
- Write a simple evaluation runner. Done for no-API context-rule checks.
- Save results as JSON or Markdown. Done; reports are written to `evals/results/`.
- Add a README section showing example eval results.

Status: in progress. The project now has deterministic evaluations for story data and source-tag rules. The next evaluation layer should run model responses against the same cases and score canon fidelity, character consistency, age appropriateness, and retrieval relevance.

Resume value:

> Built an evaluation suite for measuring canon fidelity, role consistency, and retrieval grounding in narrative AI responses.

## Phase 6: Larger Story Worlds

Goal: support longer plots and richer worlds without tying the public demo to copyrighted IP.

Good public demo candidates:

- Alice in Wonderland
- Dracula
- Sherlock Holmes
- Pride and Prejudice
- The Wonderful Wizard of Oz
- Greek mythology
- Arthurian legends
- original short stories

For larger worlds, add:

- locations
- factions
- relationship graphs
- arcs or chapters
- character-specific knowledge
- source citations

Example structure:

```text
worlds/
  wonderland/
    metadata.json
    sources/
    characters/
    timeline.json
    locations.json
    relationships.json
```

This allows private experimentation with complex fandom-scale worlds while keeping the public portfolio version legally cleaner.

## Phase 7: MCP Server

Goal: expose the story engine through a standard tool interface.

The MCP server can expose:

Resources:

- story source text
- character profiles
- timeline events
- locations
- relationship data

Tools:

- `list_stories`
- `list_characters`
- `search_story`
- `get_character_profile`
- `get_timeline_events`
- `get_character_knowledge`
- `check_canon`

Prompts:

- `roleplay_as_character`
- `retell_scene_from_pov`
- `explain_character_motivation`
- `continue_scene`

This turns POVTales from an app into reusable narrative infrastructure.

Resume value:

> Built an MCP server exposing story resources, character profiles, timeline-aware retrieval, and canon-checking tools for AI storytelling clients.

## Phase 8: Multi-Agent Orchestration

Goal: separate responsibilities so the system is easier to reason about.

Possible agents:

- Character Agent: writes in the selected character's voice.
- Retriever Agent: finds relevant canon.
- Canon Judge Agent: checks contradictions.
- Age Adapter Agent: simplifies language for the reader.
- Narrator Agent: summarizes or retells scenes.

This phase should come after evaluations, because agentic systems need good tests to avoid becoming hard to debug.

## Phase 9: Polished Demo

Goal: make the project feel like a finished portfolio piece.

Tasks:

- Add story cards or a cleaner story selector.
- Add mode tabs for Chat, Retell, Explain, and Continue.
- Add optional citations or retrieved passages.
- Add example conversations in the README.
- Add screenshots or a short demo video.
- Deploy a limited public demo if API key handling is solved.

## Suggested Build Order

1. Convert Snow White into a story package.
2. Add dynamic story and character loading.
3. Add one more public-domain story.
4. Add character profiles.
5. Add timeline-tagged source passages.
6. Add full-story retrieval.
7. Add canon validation.
8. Add evaluations.
9. Add MCP server.
10. Add multi-agent orchestration.

## Near-Term Next Step

The next implementation step should be:

> Continue Phase 4 by adding clearer response modes and better retrieved-source attribution.

The foundation is now ready for richer character responses, stronger canon checks, and larger story packages.
