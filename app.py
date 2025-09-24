import asyncio
import streamlit as st
from app.agent import StoryTimeConversationalAgent

st.set_page_config(
    page_title="StoryTime",
    page_icon="📚",
    layout="centered",
)

st.title("📚 StoryTime")
st.caption("Create personalized children's books with AI")


@st.cache_resource
def get_agent():
    return StoryTimeConversationalAgent()


async def init_agent():
    agent = get_agent()
    await agent.initialize()
    return agent


if "agent" not in st.session_state:
    with st.spinner("Initializing StoryTime..."):
        st.session_state.agent = asyncio.run(init_agent())

if "session_id" not in st.session_state:
    st.session_state.session_id = asyncio.run(st.session_state.agent.create_new_session())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I'm StoryTime, and I'm here to help create a personalized book for your child! 📖✨\n\nTo get started, could you tell me your child's name?"
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Tell me about your child..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = asyncio.run(
                    st.session_state.agent.chat(st.session_state.session_id, prompt)
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception:
                error_msg = "I'm sorry, I encountered an error. Please try again."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

with st.sidebar:
    st.header("Session Info")
    st.write(f"Session ID: {st.session_state.session_id[:8]}...")

    if st.button("Start New Conversation"):
        st.session_state.session_id = asyncio.run(st.session_state.agent.create_new_session())
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm StoryTime, and I'm here to help create a personalized book for your child! 📖✨\n\nTo get started, could you tell me your child's name?"
            }
        ]
        st.rerun()
