import json
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
    timeline: list[dict]


def load_story_packages(stories_dir: Path = STORIES_DIR) -> dict[str, StoryPackage]:
    packages = {}

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
        timeline = _read_json(timeline_path)

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
