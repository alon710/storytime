import streamlit as st
import asyncio
from src.schemas.state import ChatState, Message
from src.schemas.image import ImageRequest
from src.schemas.approval import NeedsApproval, Finalized
from src.agents.conversation_agent import process_request
from src.settings import settings

settings = settings


def main():
    st.set_page_config(page_title="Storytime Image Generator", layout="wide")
    st.title("AI Image Generator")

    if "chat_state" not in st.session_state:
        st.session_state.chat_state = ChatState()

    if "session_ended" not in st.session_state:
        st.session_state.session_ended = False

    chat_state = st.session_state.chat_state

    for message in chat_state.messages:
        with st.chat_message(message.role):
            st.write(message.text)
            if message.image_path:
                st.image(message.image_path)

    if not st.session_state.session_ended:
        col1, col2, col3 = st.columns(3)

        with col1:
            uploaded_file = st.file_uploader("Upload seed image", type=["png", "jpg", "jpeg"])

        with col2:
            style = st.selectbox("Style", ["photoreal", "watercolor", "comic"])

        with col3:
            age = st.number_input("Age", min_value=1, max_value=100, value=25)

        gender = st.radio("Gender", ["male", "female"])

        user_input = st.chat_input("Enter your message or approval...")

        if user_input and uploaded_file:
            seed_path = f"/tmp/{uploaded_file.name}"
            with open(seed_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            chat_state.messages.append(Message(role="user", text=user_input))

            with st.chat_message("user"):
                st.write(user_input)

            request = ImageRequest(seed_image_path=seed_path, style=style, age=age, gender=gender)

            try:
                result = asyncio.run(process_request(request, chat_state))

                if isinstance(result, NeedsApproval):
                    response_text = f"I've generated an image with {result.params_used}. Do you approve?"
                    chat_state.messages.append(
                        Message(role="assistant", text=response_text, image_path=result.image_path)
                    )

                    with st.chat_message("assistant"):
                        st.write(response_text)
                        st.image(result.image_path)

                elif isinstance(result, Finalized):
                    chat_state.messages.append(Message(role="assistant", text=result.message))

                    with st.chat_message("assistant"):
                        st.write(result.message)

                    st.session_state.session_ended = True
                    st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")

    else:
        st.success("Conversation has ended. Refresh to start a new session.")


if __name__ == "__main__":
    main()
