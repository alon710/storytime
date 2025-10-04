import streamlit as st
import uuid
from ai.agent import ConversationalAgent
from core.settings import settings
from core.logger import logger
from schemas.ui import ChatMessage, Status


def initialize_session_state():
    EMPTY_STATE = {
        "agent": ConversationalAgent,
        "messages": list,
        "session_id": lambda: str(uuid.uuid4()),
    }

    for key, value in EMPTY_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value()

    if not st.session_state.messages:
        initial_message = ChatMessage(
            role="assistant",
            content=settings.conversational_agent.initial_message,
        )
        st.session_state.messages.append(initial_message.model_dump())
        logger.info("Initial welcome message added to session.", session_id=st.session_state.session_id)

    logger.info("Session state initialized.", session_id=st.session_state.session_id)


def load_conversation_history():
    message_count = len(st.session_state.messages)
    logger.info("Loading conversation history.", message_count=message_count)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message.get("status") == Status.ERROR.value:
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
        text: str = prompt.text or ""
        files: list = prompt.files or []

        # Skip processing if both text and files are empty
        if not text.strip() and not files:
            logger.warning("Empty submission ignored - no text or files provided")
            return

        # For file-only uploads, use placeholder text
        if not text.strip() and files:
            text = f"[Uploaded {len(files)} file(s)]"

        logger.info("User message received.", has_files=bool(files))

        st.chat_message("user").markdown(text)
        user_message = ChatMessage(role="user", content=text)
        st.session_state.messages.append(user_message.model_dump())

        with st.chat_message("assistant"):
            with st.spinner("Loading..."):
                response = st.session_state.agent.chat(
                    text,
                    files=files,
                    session_id=st.session_state.session_id,
                )

            if response.status == Status.ERROR:
                logger.error("Agent response error.", error_message=response.message)
                st.error(response.message)
            else:
                logger.info("Agent response successful.", has_images=bool(response.images))
                st.markdown(response.message)

                if response.images:
                    for image_path in response.images:
                        st.image(image_path)

        assistant_message = ChatMessage(
            role="assistant",
            content=response.message,
            status=response.status,
            images=response.images if response.images else None,
        )
        st.session_state.messages.append(assistant_message.model_dump())
