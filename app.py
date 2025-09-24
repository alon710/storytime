import asyncio
import streamlit as st
from app.agent import StoryTimeConversationalAgent

st.set_page_config(
    page_title="StoryTime",
    page_icon="👶",
    layout="centered",
)

st.title("StoryTime")
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
    st.session_state.session_id = asyncio.run(
        st.session_state.agent.create_new_session()
    )

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I'm StoryTime, and I'm here to help create a personalized book for your child! 📖✨\n\nTo get started, could you tell me your child's name?",
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Tell me about your child...", accept_file="multiple"):
    # Handle ChatInputValue object from Streamlit
    if hasattr(user_input, "text") and hasattr(user_input, "files"):
        # ChatInputValue object from accept_file mode
        prompt = user_input.text
        uploaded_files = user_input.files
    elif isinstance(user_input, dict):
        # Dict format (fallback)
        prompt = user_input.get("text", "")
        uploaded_files = user_input.get("files", [])
    else:
        # String format (when no files uploaded)
        prompt = str(user_input)
        uploaded_files = []

    # Display user message
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "files": uploaded_files}
    )
    with st.chat_message("user"):
        st.markdown(prompt)
        # Display uploaded images
        if uploaded_files:
            st.write(f"📎 {len(uploaded_files)} image(s) uploaded:")
            for i, file in enumerate(uploaded_files):
                if file.type.startswith("image/"):
                    st.image(file, caption=f"Image {i + 1}: {file.name}", width=200)

    # Store images in session state for the agent
    if "uploaded_images" not in st.session_state:
        st.session_state.uploaded_images = []

    if uploaded_files:
        # Convert uploaded files to PIL Images and store them
        from PIL import Image
        import io

        for file in uploaded_files:
            if file.type.startswith("image/"):
                image = Image.open(io.BytesIO(file.read()))
                st.session_state.uploaded_images.append(
                    {"image": image, "name": file.name, "type": file.type}
                )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Pass images to the agent if available
                images_for_agent = (
                    [img["image"] for img in st.session_state.uploaded_images]
                    if st.session_state.uploaded_images
                    else None
                )

                response = asyncio.run(
                    st.session_state.agent.chat(
                        st.session_state.session_id,
                        prompt,
                        reference_images=images_for_agent,
                    )
                )

                # Clean up response to remove broken markdown images
                import re

                clean_response = re.sub(r"!\[.*?\]\(sandbox:.*?\)", "", response)
                clean_response = re.sub(r"!\[.*?\]\(/var/.*?\)", "", clean_response)
                clean_response = clean_response.strip()

                # Display the cleaned response
                st.markdown(clean_response)

                # Check if a seed image was generated and display it
                seed_status = asyncio.run(
                    st.session_state.agent.session_manager.get_seed_approval_status(
                        st.session_state.session_id
                    )
                )

                if seed_status["seed_generated"] and seed_status["seed_path"]:
                    import os

                    seed_path = seed_status["seed_path"]

                    if os.path.exists(seed_path):
                        # Check if we've already shown this image
                        if "displayed_seed_images" not in st.session_state:
                            st.session_state.displayed_seed_images = set()

                        if seed_path not in st.session_state.displayed_seed_images:
                            st.write("**Here's the character seed image:**")
                            st.image(
                                seed_path, caption="Character Seed Image", width=300
                            )
                            st.write(
                                "Does this look like your child? Please let me know if I should proceed or if you'd like me to try again!"
                            )
                            st.session_state.displayed_seed_images.add(seed_path)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            except Exception:
                error_msg = "I'm sorry, I encountered an error. Please try again."
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

with st.sidebar:
    st.header("Session Info")
    st.write(f"Session ID: {st.session_state.session_id[:8]}...")

    if st.button("Start New Conversation"):
        st.session_state.session_id = asyncio.run(
            st.session_state.agent.create_new_session()
        )
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm StoryTime, and I'm here to help create a personalized book for your child! 📖✨\n\nTo get started, could you tell me your child's name?",
            }
        ]
        st.rerun()
