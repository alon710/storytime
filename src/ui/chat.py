import streamlit as st
import uuid
from ai.agent import PirateAgent
from core.settings import settings
from core.logger import logger


def initialize_session_state():
    EMPTY_STATE = {
        "agent": PirateAgent,
        "messages": list,
        "session_id": lambda: str(uuid.uuid4()),
    }

    for key, value in EMPTY_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value()

    logger.info("Session state initialized.", session_id=st.session_state.session_id)


def load_conversation_history():
    message_count = len(st.session_state.messages)
    logger.info("Loading conversation history.", message_count=message_count)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message.get("status") == "error":
                st.error(message["content"])
            else:
                st.markdown(message["content"])


def render_chat():
    initialize_session_state()
    load_conversation_history()

    if prompt := st.chat_input(settings.chat.placeholder, accept_file="multiple"):
        logger.info("User message received.")
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Loading..."):
                response = st.session_state.agent.chat(prompt, session_id=st.session_state.session_id)

            if response.status == "error":
                logger.error("Agent response error.", error_message=response.message)
                st.error(response.message)
            else:
                logger.info("Agent response successful.")
                st.markdown(response.message)

        st.session_state.messages.append({"role": "assistant", "content": response.message, "status": response.status})
