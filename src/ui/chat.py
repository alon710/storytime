import streamlit as st
from ai.agent import PirateAgent


def run_chat():
    st.set_page_config(page_title="Pirate Chat", page_icon="🏴‍☠️")
    st.title("🏴‍☠️ Chat with Captain Blackbeard")

    # Initialize the agent
    if "agent" not in st.session_state:
        st.session_state.agent = PirateAgent()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message.get("status") == "error":
                st.error(message["content"])
            else:
                st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What would you like to ask the pirate captain?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get response from agent
        with st.chat_message("assistant"):
            with st.spinner("Captain is thinking..."):
                response = st.session_state.agent.chat(prompt)

            if response.status == "error":
                st.error(response.message)
            else:
                st.markdown(response.message)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response.message, "status": response.status})
