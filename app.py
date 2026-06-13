import streamlit as st

from story_data import (
    STORY_PACKAGES,
    get_character_names,
    get_timeline_event_by_label,
    get_timeline_labels,
)
from utils import SPOILER_MODES, StoryChatbot


MODEL_OPTIONS = ["gpt-4o-mini", "gpt-4o", "gpt-5-nano", "gpt-5-mini"]


st.set_page_config(page_title="POVTales", layout="wide")

st.title("POVTales")
st.caption("Chat with a story character and hear the tale from their point of view.")

if not STORY_PACKAGES:
    st.error("No story packages were found in the stories directory.")
    st.stop()

with st.sidebar:
    st.header("API Key")
    api_key = st.text_input("OpenAI API key", type="password")

    st.header("Story Setup")
    story = st.selectbox("Story", list(STORY_PACKAGES.keys()))
    selected_story = STORY_PACKAGES[story]
    timeline_labels = get_timeline_labels(selected_story)
    if not timeline_labels:
        st.error(f"{story} does not have any timeline events.")
        st.stop()

    character = st.selectbox("Character", get_character_names(selected_story))
    timeline_label = st.selectbox(
        "Story moment",
        timeline_labels,
        index=len(timeline_labels) - 1,
    )
    spoiler_mode = st.selectbox("Spoiler setting", SPOILER_MODES, index=0)
    age = st.number_input("Reader age", min_value=3, max_value=18, value=8, step=1)
    model = st.selectbox("Model", MODEL_OPTIONS, index=0)

    if st.button("Start over", use_container_width=True):
        st.session_state.pop("chatbot", None)
        st.session_state.pop("chatbot_config", None)
        st.session_state.messages = []

if not api_key:
    st.warning("Please enter your OpenAI API key to start chatting.")
    st.stop()

timeline_event = get_timeline_event_by_label(selected_story, timeline_label)
chatbot_config = {
    "story": story,
    "role": character,
    "timeline_event_id": timeline_event.id,
    "spoiler_mode": spoiler_mode,
    "age": age,
    "model": model,
    "api_key": api_key,
}

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.get("chatbot_config") != chatbot_config:
    st.session_state.chatbot = StoryChatbot(**chatbot_config)
    st.session_state.chatbot_config = chatbot_config
    st.session_state.messages = []

chatbot = st.session_state.chatbot

st.info(
    f"You are speaking with **{character}** from **{story}** at "
    f"**moment {timeline_event.order}** with **{spoiler_mode.lower()}**."
)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"Speak to {character}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"{character} is thinking..."):
            response = chatbot.respond(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
