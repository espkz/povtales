import streamlit as st

from story_data import (
    STORY_PACKAGES,
    get_character_names,
)
from utils import StoryChatbot, normalize_api_key


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
    try:
        api_key = normalize_api_key(api_key)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    st.header("Story Setup")
    story = st.selectbox("Story", list(STORY_PACKAGES.keys()))
    selected_story = STORY_PACKAGES[story]
    if not selected_story.timeline:
        st.error(f"{story} does not have any timeline events.")
        st.stop()

    character = st.selectbox("Character", get_character_names(selected_story))
    age = st.number_input("Reader age", min_value=3, max_value=18, value=8, step=1)
    model = st.selectbox("Model", MODEL_OPTIONS, index=0)

    validate_responses = False
    show_grounding = False

    with st.expander("Advanced"):
        validate_responses = st.checkbox("Validate responses", value=False)
        show_grounding = st.checkbox("Show grounding details", value=False)

    if st.button("Start over", use_container_width=True):
        st.session_state.pop("chatbot", None)
        st.session_state.pop("chatbot_config", None)
        st.session_state.messages = []

if not api_key:
    st.warning("Please enter your OpenAI API key to start chatting.")
    st.stop()

chatbot_config = {
    "story": story,
    "role": character,
    "age": age,
    "model": model,
    "api_key": api_key,
    "validate_responses": validate_responses,
}

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.get("chatbot_config") != chatbot_config:
    try:
        st.session_state.chatbot = StoryChatbot(**chatbot_config)
    except Exception as exc:
        st.error("POVTales could not start the selected chat.")
        st.exception(exc)
        st.stop()
    st.session_state.chatbot_config = chatbot_config
    st.session_state.messages = []

chatbot = st.session_state.chatbot

st.info(f"You are speaking with **{character}** from **{story}**.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"Speak to {character}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"{character} is thinking..."):
            try:
                response = chatbot.respond(prompt)
            except Exception as exc:
                st.error("POVTales could not generate a response.")
                st.exception(exc)
                st.stop()
        st.markdown(response)
        if show_grounding:
            with st.expander("Grounding details"):
                st.markdown("**Source Context**")
                st.code(chatbot.last_context or "No context recorded.")
                if chatbot.last_validation is not None:
                    st.markdown("**Validation**")
                    st.json(
                        {
                            "passed": chatbot.last_validation.passed,
                            "revised": chatbot.last_validation.revised,
                            "issues": chatbot.last_validation.issues,
                        }
                    )

    st.session_state.messages.append({"role": "assistant", "content": response})
