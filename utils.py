from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain import PromptTemplate
from langchain.chains import LLMChain


embeddings = OpenAIEmbeddings()


def get_response(user_input):
    llm = OpenAI(model_name="text-davinci-003")

    prompt = PromptTemplate(
        input_variables=["question", "docs"],
        template="""
        """,
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    response = chain.run(input=user_input)
    response = response.replace("\n", "")
    return response