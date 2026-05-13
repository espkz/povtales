# POVTales

What if stories were told from the perspective of the characters?

POVTales is a small Streamlit app for chatting with story characters. The chatbot uses retrieval over the source story so characters can answer in a way that stays grounded in the original text.

## Current Features

- Chat with a selected character from a story
- Retrieve relevant story passages before each response
- Adapt language for a reader's age
- Keep the character's point of view during conversation
- Load story metadata, characters, and timelines from story packages

## Project Roadmap

See [ROADMAP.md](ROADMAP.md) for the planned path toward multi-story support, timeline-aware roleplay, canon validation, evaluations, and an MCP server.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Enter your OpenAI API key in the sidebar when the app opens.

## Story Packages

Stories live in folders under `stories/`:

```text
stories/
  snow_white/
    source.txt
    metadata.json
    characters.json
    timeline.json
```

The app discovers story packages automatically as long as all four files exist.

## Included Stories

- [Snow White](https://www.dltk-teach.com/rhymes/snowwhite/story.htm)
  - Snow White
  - Prince
  - Queen
  - Hunter
- [Sleeping Beauty](https://www.grimmstories.com/en/grimm_fairy-tales/sleeping_beauty)
  - Rosamond (Sleeping Beauty)
  - Thirteenth Wise Woman
  - King
  - Prince
