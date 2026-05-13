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
    get_character_profile,
)


BASE_DIR = Path(__file__).resolve().parent


class StoryChatbot:
    def __init__(self, story, role, age, model, api_key=None):
        if story not in STORY_PACKAGES:
            raise ValueError(f"Unknown story: {story}")

        self.story_package = STORY_PACKAGES[story]
        self.character_profile = get_character_profile(self.story_package, role)

        self.story = story
        self.role = role
        self.age = age
        self.history = []

        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        self.db = self.create_story_db(self.story_package.source_path)
        self.retriever = self.db.as_retriever(search_kwargs={"k": 4})
        self.llm = ChatOpenAI(model=model, api_key=api_key, temperature=0.7)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.configure_system_prompt()),
                MessagesPlaceholder(variable_name="history"),
                (
                    "system",
                    "Relevant story passages. Use these as canon and do not contradict them:\n{context}",
                ),
                ("user", "{input}"),
            ]
        )

        self.chain = self.prompt | self.llm

    def get_context(self, user_input):
        docs = self.retriever.invoke(user_input)
        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    def configure_system_prompt(self):
        prompt_path = BASE_DIR / "prompt.md"
        prompt = prompt_path.read_text(encoding="utf-8")
        return prompt.format(
            role=self.role,
            story=self.story,
            age=self.age,
            character_profile=format_character_profile(self.character_profile),
        )

    def create_story_db(self, story_path):
        loader = TextLoader(str(story_path), encoding="utf-8")
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        docs = splitter.split_documents(documents)
        return FAISS.from_documents(docs, self.embeddings)

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
