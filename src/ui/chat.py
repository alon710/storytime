import streamlit as st
import uuid
from ai.agent import ConversationalAgent
from core.settings import settings
from core.logger import logger


def initialize_session_state():
    EMPTY_STATE = {
        "agent": ConversationalAgent,
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

                if message.get("images"):
                    for image_path in message["images"]:
                        st.image(image_path)


def render_chat():
    initialize_session_state()
    load_conversation_history()

    if prompt := st.chat_input(settings.chat.placeholder, accept_file="multiple"):
        text = (prompt.text or "") if hasattr(prompt, "text") else prompt
        files = prompt.files if hasattr(prompt, "files") else []

        logger.info("User message received.", has_files=bool(files))

        st.chat_message("user").markdown(text)
        st.session_state.messages.append({"role": "user", "content": text})

        with st.chat_message("assistant"):
            with st.spinner("Loading..."):
                response = st.session_state.agent.chat(text, files=files, session_id=st.session_state.session_id)

            if response.status == "error":
                logger.error("Agent response error.", error_message=response.message)
                st.error(response.message)
            else:
                logger.info("Agent response successful.", has_images=bool(response.images))
                st.markdown(response.message)

                if response.images:
                    for image_path in response.images:
                        st.image(image_path)

        message_data = {"role": "assistant", "content": response.message, "status": response.status}
        if response.images:
            message_data["images"] = response.images

        st.session_state.messages.append(message_data)
