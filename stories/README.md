# Story Packages

Each story lives in its own folder and must include these files:

```text
source.txt
metadata.json
characters.json
timeline.json
```

The app discovers packages automatically at startup. A folder is ignored unless all four files are present.

## metadata.json

Describes the story itself:

```json
{
  "id": "snow_white",
  "title": "Snow White",
  "genre": "fairy tale",
  "source": "public domain",
  "source_url": "https://example.com",
  "recommended_age_min": 5,
  "recommended_age_max": 12,
  "description": "Short description of the story."
}
```

## characters.json

Defines the characters users can chat with:

```json
[
  {
    "id": "snow_white",
    "name": "Snow White",
    "role": "protagonist",
    "traits": ["kind", "gentle"],
    "goals": ["stay safe"],
    "voice": "warm, gentle, and sincere"
  }
]
```

## timeline.json

Lists major story events in order:

```json
[
  {
    "id": "forest_escape",
    "order": 1,
    "summary": "Snow White escapes into the forest.",
    "characters_present": ["snow_white"],
    "known_by": ["snow_white"]
  }
]
```
