from dataclasses import dataclass, field
from functools import lru_cache
import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from story_data import (
    STORY_PACKAGES,
    format_character_profile,
    format_timeline_events,
    get_events_known_by,
    get_events_until,
    get_character_profile,
)


BASE_DIR = Path(__file__).resolve().parent


@dataclass
class ValidationResult:
    passed: bool
    issues: list[dict] = field(default_factory=list)
    revised: bool = False
    raw: str = ""

    @property
    def needs_revision(self):
        return not self.passed


class StoryChatbot:
    def __init__(
        self,
        story,
        role,
        age,
        model,
        api_key=None,
        validate_responses=True,
    ):
        if story not in STORY_PACKAGES:
            raise ValueError(f"Unknown story: {story}")

        self.story_package = STORY_PACKAGES[story]
        self.character_profile = get_character_profile(self.story_package, role)

        self.story = story
        self.role = role
        self.age = age
        self.model = model
        self.api_key = api_key
        self.validate_responses = validate_responses
        self.retrievers = {}
        self.history = []
        self.last_context = ""
        self.last_validation = None
        self.story_context = self.build_story_context()

        self.llm = ChatOpenAI(model=model, api_key=api_key, temperature=0.7)
        self.validator_llm = None

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.configure_system_prompt()),
                MessagesPlaceholder(variable_name="history"),
                (
                    "system",
                    "Source context. Use this as canon and do not contradict it:\n{context}",
                ),
                ("user", "{input}"),
            ]
        )

        self.chain = self.prompt | self.llm
        self.validation_chain = None
        self.revision_chain = None

    def get_context(self, user_input):
        if not self.story_package.passages:
            return (
                "No raw source passages are available. Use the story context from "
                "the system instructions."
            )

        retriever = self.get_retriever()
        if retriever is None:
            return (
                "No source passages are available. Use the story context from the "
                "system instructions."
            )

        docs = retriever.invoke(user_input)
        source_context = "\n\n---\n\n".join(
            format_retrieved_passage(doc)
            for doc in docs
        )
        return "Relevant source passages:\n" + source_context

    def get_retriever(self):
        cache_key = self.story_package.id
        if cache_key not in self.retrievers:
            db = create_story_db(
                self.story_package.id,
                self.api_key,
            )
            self.retrievers[cache_key] = (
                db.as_retriever(search_kwargs={"k": 4})
                if db is not None
                else None
            )

        return self.retrievers[cache_key]

    def configure_system_prompt(self):
        prompt_path = BASE_DIR / "prompt.md"
        prompt = prompt_path.read_text(encoding="utf-8")
        return prompt.format(
            role=self.role,
            story=self.story,
            age=self.age,
            character_profile=format_character_profile(self.character_profile),
            story_context=self.get_story_context(),
        )

    def get_story_context(self):
        return self.story_context

    def build_story_context(self):
        known_events = get_events_known_by(
            self.story_package,
            self.character_profile.id,
            None,
        )
        full_story_events = get_events_until(self.story_package, None)

        return "\n".join(
            [
                "Full story timeline:",
                format_timeline_events(full_story_events),
                "",
                "Events this character personally knows or experiences:",
                format_timeline_events(known_events),
            ]
        )

    def respond(self, user_input):
        clean_input = user_input.strip()
        context = self.get_context(clean_input)
        self.last_context = context

        result = self.chain.invoke(
            {
                "input": clean_input,
                "history": self.history,
                "context": context,
            }
        )
        response = result.content
        validation = ValidationResult(passed=True)

        if self.validate_responses:
            validation = self.validate_response(clean_input, response, context)
            if validation.needs_revision:
                response = self.revise_response(
                    clean_input,
                    response,
                    context,
                    validation,
                )
                validation.revised = True

        self.history.append(HumanMessage(content=clean_input))
        self.history.append(AIMessage(content=response))
        self.last_validation = validation
        return response

    def validate_response(self, user_input, response, context):
        if self.validation_chain is None:
            self.validator_llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                temperature=0,
            )
            self.validation_chain = build_validation_prompt() | self.validator_llm

        result = self.validation_chain.invoke(
            self.build_validation_payload(user_input, response, context)
        )
        return parse_validation_result(result.content)

    def revise_response(self, user_input, response, context, validation):
        if self.revision_chain is None:
            self.revision_chain = build_revision_prompt() | self.llm

        payload = self.build_validation_payload(user_input, response, context)
        payload["issues"] = format_validation_issues(validation.issues)
        result = self.revision_chain.invoke(payload)
        return result.content

    def build_validation_payload(self, user_input, response, context):
        return {
            "story": self.story,
            "role": self.role,
            "age": self.age,
            "story_context": self.get_story_context(),
            "source_context": context,
            "user_input": user_input,
            "response": response,
        }


@lru_cache(maxsize=32)
def create_story_db(story_id, api_key=None):
    story = next(
        story
        for story in STORY_PACKAGES.values()
        if story.id == story_id
    )
    passages = story.passages
    if not passages:
        return None

    documents = [
        Document(
            page_content=passage.text,
            metadata={
                "event_id": passage.event_id,
                "event_order": passage.event_order,
                "story_id": story.id,
            },
        )
        for passage in passages
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    docs = splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(api_key=api_key)
    return FAISS.from_documents(docs, embeddings)


def format_retrieved_passage(doc):
    event_id = doc.metadata.get("event_id", "unknown")
    event_order = doc.metadata.get("event_order", "?")
    return f"[event {event_order}: {event_id}]\n{doc.page_content}"


def build_validation_prompt():
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "\n".join(
                    [
                        "You are a strict canon validator for POVTales.",
                        "Decide whether the draft response is safe to show.",
                        "Use only the story context and source passages as canon.",
                        "Check for canon contradictions, point-of-view problems, and age/tone problems.",
                        "Allow character-grounded imagination for hypotheticals, motives, feelings, and possibilities.",
                        "Do not fail a response just because it speculates, as long as speculation is not presented as confirmed canon.",
                        "Return JSON only with this shape:",
                        '{"passed": true, "issues": []}',
                        "If it fails, use this shape:",
                        '{"passed": false, "issues": [{"type": "canon", "description": "short reason"}]}',
                        "Issue types must be one of: canon, pov, age, tone.",
                    ]
                ),
            ),
            (
                "user",
                "\n\n".join(
                    [
                        "Story: {story}",
                        "Character: {role}",
                        "Reader age: {age}",
                        "Story context:\n{story_context}",
                        "Source passages:\n{source_context}",
                        "User message:\n{user_input}",
                        "Draft response:\n{response}",
                    ]
                ),
            ),
        ]
    )


def build_revision_prompt():
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "\n".join(
                    [
                        "You revise character responses for POVTales.",
                        "Keep the same character voice, but fix every listed validation issue.",
                        "Use only the story context and source passages as canon.",
                        "Preserve character-grounded imagination when it does not contradict canon.",
                        "Keep the response age-appropriate for the reader.",
                        "Return only the revised character response.",
                    ]
                ),
            ),
            (
                "user",
                "\n\n".join(
                    [
                        "Story: {story}",
                        "Character: {role}",
                        "Reader age: {age}",
                        "Story context:\n{story_context}",
                        "Source passages:\n{source_context}",
                        "User message:\n{user_input}",
                        "Validation issues:\n{issues}",
                        "Draft response:\n{response}",
                    ]
                ),
            ),
        ]
    )


def parse_validation_result(raw_content):
    try:
        data = json.loads(extract_json_object(raw_content))
    except (TypeError, ValueError, json.JSONDecodeError):
        return ValidationResult(
            passed=False,
            issues=[
                {
                    "type": "canon",
                    "description": "Validator did not return parseable JSON.",
                }
            ],
            raw=raw_content,
        )

    issues = data.get("issues", [])
    if not isinstance(issues, list):
        issues = [
            {
                "type": "canon",
                "description": "Validator returned malformed issues.",
            }
        ]

    passed = bool(data.get("passed", False)) and not issues
    return ValidationResult(passed=passed, issues=issues, raw=raw_content)


def extract_json_object(text):
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found.")

    return stripped[start : end + 1]


def format_validation_issues(issues):
    if not issues:
        return "None."

    return "\n".join(
        f"- {issue.get('type', 'unknown')}: {issue.get('description', '')}"
        for issue in issues
    )
