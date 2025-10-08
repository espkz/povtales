from langgraph.checkpoint.memory import MemorySaver

from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough

embeddings = OpenAIEmbeddings()
memory = MemorySaver()

class StoryChatbot():
    def __init__(self, story, role, age, model):
        self.db = self.create_story_db(story)
        self.retriever = self.db.as_retriever(search_kwargs={"k" : 3})
        self.story = story
        self.role = role
        self.age = age

        self.system_prompt = self.configure_system_prompt()

        self.llm = ChatOpenAI(model=model)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}"),
            ("system", "Relevant context:\n{context}")
        ])

        self.chain =  (
            RunnableParallel(
                {
                    "input" : RunnablePassthrough(),
                    "history" : lambda x: memory.load_memory_variables({})["history"],
                    "context" : self.get_context
                }
            )
        )

    def get_context(self, user_input):
        docs = self.retriever.get_relevant_documents(user_input["input"])
        return {"context" : "\n".join([d.page_content for d in docs])}


    def configure_system_prompt(self):
        with open('prompt.md', 'r') as f:
            prompt = f.read()
        prompt.format(role=self.role, story=self.story, age=self.age)
        return prompt


    def create_story_db(self, story_path : str) -> FAISS:
        loader = TextLoader(story_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap= 100)
        docs = splitter.split_documents(documents)

        db = FAISS.from_documents(docs, embeddings)
        return db

    def respond(self, user_input):
        result = self.chain.invoke({"input" : user_input})
        return result.content