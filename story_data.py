import json
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
STORIES_DIR = BASE_DIR / "stories"


@dataclass(frozen=True)
class CharacterProfile:
    id: str
    name: str
    role: str
    traits: list[str]
    goals: list[str]
    voice: str


@dataclass(frozen=True)
class TimelineEvent:
    id: str
    order: int
    summary: str
    characters_present: list[str]
    known_by: list[str]


@dataclass(frozen=True)
class SourcePassage:
    event_id: str
    event_order: int
    text: str


@dataclass(frozen=True)
class StoryPackage:
    id: str
    title: str
    genre: str
    source: str
    source_url: str
    recommended_age_min: int
    recommended_age_max: int
    description: str
    source_path: Path
    characters: list[CharacterProfile]
    timeline: list[TimelineEvent]
    passages: list[SourcePassage]


def load_story_packages(stories_dir: Path = STORIES_DIR) -> dict[str, StoryPackage]:
    packages = {}

    if not stories_dir.exists():
        return packages

    for story_dir in sorted(path for path in stories_dir.iterdir() if path.is_dir()):
        metadata_path = story_dir / "metadata.json"
        characters_path = story_dir / "characters.json"
        timeline_path = story_dir / "timeline.json"
        source_path = story_dir / "source.txt"

        if not all(
            path.exists()
            for path in [metadata_path, characters_path, timeline_path, source_path]
        ):
            continue

        metadata = _read_json(metadata_path)
        character_data = _read_json(characters_path)
        timeline_data = _read_json(timeline_path)

        characters = [
            CharacterProfile(
                id=item["id"],
                name=item["name"],
                role=item["role"],
                traits=item.get("traits", []),
                goals=item.get("goals", []),
                voice=item.get("voice", ""),
            )
            for item in character_data
        ]
        timeline = [
            TimelineEvent(
                id=item["id"],
                order=item["order"],
                summary=item["summary"],
                characters_present=item.get("characters_present", []),
                known_by=item.get("known_by", []),
            )
            for item in timeline_data
        ]
        timeline = sorted(timeline, key=lambda event: event.order)

        story = StoryPackage(
            id=metadata["id"],
            title=metadata["title"],
            genre=metadata.get("genre", ""),
            source=metadata.get("source", ""),
            source_url=metadata.get("source_url", ""),
            recommended_age_min=metadata.get("recommended_age_min", 3),
            recommended_age_max=metadata.get("recommended_age_max", 18),
            description=metadata.get("description", ""),
            source_path=source_path,
            characters=characters,
            timeline=timeline,
            passages=build_source_passages(source_path, timeline),
        )

        packages[story.title] = story

    return packages


def get_character_names(story: StoryPackage) -> list[str]:
    return [character.name for character in story.characters]


def get_character_profile(story: StoryPackage, character_name: str) -> CharacterProfile:
    for character in story.characters:
        if character.name == character_name:
            return character

    raise ValueError(f"{character_name} is not available for {story.title}")


def get_timeline_event(story: StoryPackage, event_id: str) -> TimelineEvent:
    for event in story.timeline:
        if event.id == event_id:
            return event

    raise ValueError(f"{event_id} is not a timeline event for {story.title}")


def get_events_until(story: StoryPackage, event_id: str | None) -> list[TimelineEvent]:
    if not story.timeline:
        return []

    if event_id is None:
        return sorted(story.timeline, key=lambda event: event.order)

    selected_event = get_timeline_event(story, event_id)
    return [
        event
        for event in sorted(story.timeline, key=lambda event: event.order)
        if event.order <= selected_event.order
    ]


def get_events_known_by(
    story: StoryPackage,
    character_id: str,
    event_id: str | None,
) -> list[TimelineEvent]:
    return [
        event
        for event in get_events_until(story, event_id)
        if character_id in event.known_by
    ]


def format_timeline_events(events: list[TimelineEvent]) -> str:
    if not events:
        return "None yet."

    return "\n".join(
        f"- {event.order}. {event.summary}"
        for event in sorted(events, key=lambda event: event.order)
    )


def build_source_passages(
    source_path: Path,
    timeline: list[TimelineEvent],
) -> list[SourcePassage]:
    if not timeline:
        return []

    paragraphs = split_source_text(
        source_path.read_text(encoding="utf-8"),
        min_passages=len(timeline),
    )
    if not paragraphs:
        return []

    passages = []
    events = sorted(timeline, key=lambda event: event.order)

    for index, paragraph in enumerate(paragraphs):
        event_index = min(
            len(events) - 1,
            index * len(events) // len(paragraphs),
        )
        event = events[event_index]
        passages.append(
            SourcePassage(
                event_id=event.id,
                event_order=event.order,
                text=paragraph,
            )
        )

    return passages


def split_source_text(source_text: str, min_passages: int) -> list[str]:
    paragraphs = [
        paragraph.strip()
        for paragraph in source_text.split("\n\n")
        if paragraph.strip()
    ]
    if len(paragraphs) >= min_passages:
        return paragraphs

    lines = [
        line.strip()
        for line in source_text.splitlines()
        if line.strip()
    ]
    if len(lines) >= min_passages:
        return lines

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", source_text)
        if sentence.strip()
    ]
    return sentences or paragraphs


def format_character_profile(character: CharacterProfile) -> str:
    traits = ", ".join(character.traits) or "not specified"
    goals = ", ".join(character.goals) or "not specified"

    return "\n".join(
        [
            f"Name: {character.name}",
            f"Story role: {character.role}",
            f"Traits: {traits}",
            f"Goals: {goals}",
            f"Voice: {character.voice or 'not specified'}",
        ]
    )


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


STORY_PACKAGES = load_story_packages()
