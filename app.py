import streamlit as st
from utils import StoryChatbot
from openai import OpenAI

st.set_page_config(page_title="Story Chatbot", layout="wide")

st.title("Story Chatbot")
st.caption("Chat with a story character, powered by LangChain")

# functions

def test_client(api_key):
    client = OpenAI(api_key=api_key)
    try:
        client.models.list()
        return True
    except Exception:
        return False


# sidebar
st.sidebar.header("🔑 API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

if not api_key:
    st.warning("Please enter your OpenAI API key to start chatting.")
    st.stop()

if st.session_state.get('api_key', '') != api_key:
    if not test_client(api_key):
        st.session_state['api_key'] = ''
        st.warning("Please enter a valid OpenAI API key.")
    else:
        st.session_state['api_key'] = api_key
        st.info("Your OpenAI API key is validated")

st.sidebar.header("Configuration")
story = st.sidebar.selectbox("Choose a story", ["Snow White"])
chr = st.sidebar.selectbox("Choose a character", ["Snow White", "Prince", "Queen", "Hunter"])
age = st.sidebar.number_input("What's your age?", min_value=3, max_value=18, value=8, step=1)
# for the sake of cost using gpt-5-nano is the best
model = st.sidebar.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-5-nano", "gpt-5-mini"])

# set character and age
if "selected_character" not in st.session_state:
    st.session_state.selected_character = chr

if "selected_age" not in st.session_state:
    st.session_state.selected_age = age

if "chatbot" not in st.session_state:
    st.session_state.chatbot = StoryChatbot(story=story, role=chr, age=age, model=model, api_key=api_key)
    st.session_state.messages = []

chatbot = st.session_state.chatbot

# detect character change
character_changed = chr != st.session_state.selected_character
age_changed = age != st.session_state.selected_age

if character_changed:
    chatbot.set_character(chr, age)
    st.session_state.messages.append({
        "role": "system",
        "content": f"Switched character to **{chr}**."
    })
    st.session_state.selected_character = chr
if age_changed:
    chatbot.set_character(chr, age)
    st.session_state.selected_age = age

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Speak to the character!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = chatbot.respond(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
