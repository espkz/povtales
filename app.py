import os
from pathlib import Path

import streamlit as st

from story_data import (
    STORY_PACKAGES,
    get_character_names,
)
from utils import RESPONSE_MODES, StoryChatbot, normalize_api_key


MODEL_OPTIONS = ["gpt-4o-mini", "gpt-4o", "gpt-5-nano", "gpt-5-mini"]
ENV_PATH = Path(__file__).resolve().parent / ".env"


def get_configured_api_key():
    return (
        os.environ.get("OPENAI_API_KEY")
        or get_streamlit_secret("OPENAI_API_KEY")
        or get_dotenv_value("OPENAI_API_KEY")
        or ""
    )


def get_streamlit_secret(key):
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


def get_dotenv_value(key):
    if not ENV_PATH.exists():
        return ""

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() == key:
            return value.strip().strip("\"'")

    return ""


st.set_page_config(page_title="POVTales", layout="wide")

st.title("POVTales")
st.caption("Chat with a story character and hear the tale from their point of view.")

if not STORY_PACKAGES:
    st.error("No story packages were found in the stories directory.")
    st.stop()

with st.sidebar:
    st.header("API Key")
    configured_api_key = get_configured_api_key()
    api_key = st.text_input(
        "OpenAI API key",
        value=configured_api_key,
        type="password",
    )
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
    response_mode = st.selectbox("Mode", RESPONSE_MODES, index=0)
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
    "response_mode": response_mode,
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
                st.markdown("**Retrieved Sources**")
                if chatbot.last_sources:
                    for index, source in enumerate(chatbot.last_sources, start=1):
                        st.markdown(
                            f"{index}. Event {source['event_order']}: "
                            f"`{source['event_id']}`"
                        )
                        st.code(source["text"])
                else:
                    st.caption("No source passages recorded.")
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
