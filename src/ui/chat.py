import streamlit as st
from ai.agent import PirateAgent
from core.settings import settings


def initialize_session_state():
    EMPTY_STATE = {
        "agent": PirateAgent,
        "messages": list,
    }

    for key, value in EMPTY_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value()


def load_conversation_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message.get("status") == "error":
                st.error(message["content"])
            else:
                st.markdown(message["content"])


def run_chat():
    initialize_session_state()
    load_conversation_history()

    if prompt := st.chat_input(settings.chat.placeholder):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Loading..."):
                response = st.session_state.agent.chat(prompt)

            if response.status == "error":
                st.error(response.message)
            else:
                st.markdown(response.message)

        st.session_state.messages.append({"role": "assistant", "content": response.message, "status": response.status})
