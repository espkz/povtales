from functools import lru_cache
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
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
    get_timeline_event,
)


BASE_DIR = Path(__file__).resolve().parent


FULL_STORY_SPOILERS = "Full-story spoilers"
NO_SPOILERS = "No spoilers"
SPOILERS_UP_TO_SELECTED_MOMENT = "Spoilers up to selected moment"
SPOILER_MODES = [
    NO_SPOILERS,
    SPOILERS_UP_TO_SELECTED_MOMENT,
    FULL_STORY_SPOILERS,
]


class StoryChatbot:
    def __init__(
        self,
        story,
        role,
        timeline_event_id,
        spoiler_mode,
        age,
        model,
        api_key=None,
    ):
        if story not in STORY_PACKAGES:
            raise ValueError(f"Unknown story: {story}")

        self.story_package = STORY_PACKAGES[story]
        self.character_profile = get_character_profile(self.story_package, role)
        self.timeline_event = get_timeline_event(
            self.story_package,
            timeline_event_id,
        )

        self.story = story
        self.role = role
        self.timeline_event_id = timeline_event_id
        self.spoiler_mode = spoiler_mode
        self.age = age
        self.api_key = api_key
        self.retriever = None
        self.history = []

        self.llm = ChatOpenAI(model=model, api_key=api_key, temperature=0.7)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.configure_system_prompt()),
                MessagesPlaceholder(variable_name="history"),
                (
                    "system",
                    "Allowed story context. Use this as canon and do not contradict it:\n{context}",
                ),
                ("user", "{input}"),
            ]
        )

        self.chain = self.prompt | self.llm

    def get_context(self, user_input):
        if self.spoiler_mode != FULL_STORY_SPOILERS:
            return (
                "No raw source passages are included for this spoiler setting. "
                "Use the timeline and spoiler boundary from the system instructions as canon."
            )

        docs = self.get_retriever().invoke(user_input)
        source_context = "\n\n---\n\n".join(doc.page_content for doc in docs)
        return "Relevant source passages:\n" + source_context

    def get_retriever(self):
        if self.retriever is None:
            db = create_story_db(str(self.story_package.source_path), self.api_key)
            self.retriever = db.as_retriever(search_kwargs={"k": 4})

        return self.retriever

    def configure_system_prompt(self):
        prompt_path = BASE_DIR / "prompt.md"
        prompt = prompt_path.read_text(encoding="utf-8")
        return prompt.format(
            role=self.role,
            story=self.story,
            age=self.age,
            character_profile=format_character_profile(self.character_profile),
            timeline_context=self.get_timeline_context(),
            spoiler_mode=self.spoiler_mode,
        )

    def get_timeline_context(self):
        known_events = get_events_known_by(
            self.story_package,
            self.character_profile.id,
            self.timeline_event_id,
        )
        events_until_moment = get_events_until(
            self.story_package,
            self.timeline_event_id,
        )
        full_story_events = get_events_until(self.story_package, None)

        if self.spoiler_mode == NO_SPOILERS:
            allowed_events = known_events
            spoiler_rule = (
                "Do not reveal events outside the character-known events. "
                "If asked about unknown or future events, say you do not know yet."
            )
        elif self.spoiler_mode == SPOILERS_UP_TO_SELECTED_MOMENT:
            allowed_events = events_until_moment
            spoiler_rule = (
                "You may discuss canon events up to the selected moment, but keep "
                "your personal point of view separate from facts this character "
                "would not personally know."
            )
        else:
            allowed_events = full_story_events
            spoiler_rule = (
                "Full-story spoilers are allowed when the reader asks. When "
                "roleplaying, still distinguish what the character knows at the "
                "selected moment from full-story canon."
            )

        return "\n".join(
            [
                f"Current story moment: {self.timeline_event.order}. {self.timeline_event.summary}",
                f"Spoiler setting: {self.spoiler_mode}",
                f"Spoiler rule: {spoiler_rule}",
                "",
                "Events this character personally knows at this moment:",
                format_timeline_events(known_events),
                "",
                "Allowed canon events for this response:",
                format_timeline_events(allowed_events),
            ]
        )

    def respond(self, user_input):
        clean_input = user_input.strip()
        context = self.get_context(clean_input)

        result = self.chain.invoke(
            {
                "input": clean_input,
                "history": self.history,
                "context": context,
            }
        )

        self.history.append(HumanMessage(content=clean_input))
        self.history.append(AIMessage(content=result.content))
        return result.content


@lru_cache(maxsize=8)
def create_story_db(story_path, api_key=None):
    loader = TextLoader(story_path, encoding="utf-8")
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    docs = splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(api_key=api_key)
    return FAISS.from_documents(docs, embeddings)
