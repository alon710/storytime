"""
StoryTime - AI-Powered Children's Storybook Generator
Simple Streamlit app for creating illustrated PDF storybooks
"""

import streamlit as st
import os
from pathlib import Path
from story_processor import StoryProcessor
from config import settings


def main():
    st.set_page_config(page_title="StoryTime", page_icon="📚")

    st.title("📚 StoryTime")
    st.write("Create AI-Illustrated Children's Storybooks")

    # Check for API key
    try:
        settings.google_api_key
    except Exception as e:
        st.error("⚠️ Please set your GOOGLE_API_KEY in your .env file")
        st.info("You can get an API key from: https://makersuite.google.com/app/apikey")
        st.stop()

    # Simple form
    with st.form("storybook_form"):
        # File uploads
        pdf_file = st.file_uploader("Upload PDF Story", type=["pdf"])
        character_image = st.file_uploader(
            "Upload Character Photo", type=["jpg", "jpeg", "png"]
        )

        # Settings
        col1, col2 = st.columns(2)
        with col1:
            character_name = st.text_input("Character Name", value="Alex")
            character_age = st.number_input("Age", min_value=1, max_value=12, value=5)
            character_gender = st.selectbox("Gender", ["Boy", "Girl"])
        with col2:
            art_style = st.selectbox(
                "Art Style", ["storybook", "watercolor", "cartoon"]
            )
            language = st.selectbox("Output Language", ["English", "Hebrew"])

        # Submit
        submitted = st.form_submit_button(
            "Generate Storybook", use_container_width=True
        )

    if submitted:
        # Validation
        if not pdf_file or not character_image or not character_name.strip():
            st.error("Please provide all required inputs")
            return

        # Use current directory for output
        output_path = Path.cwd()

        # Process
        with st.spinner("Creating your storybook..."):
            processor = StoryProcessor()
            progress_bar = st.progress(0)

            results = processor.process_story(
                pdf_file=pdf_file,
                character_image=character_image,
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
                art_style=art_style,
                output_folder=str(output_path),
                language=language,
                progress_bar=progress_bar,
            )

            # Results
            if results["success"]:
                st.success("🎉 Storybook created!")
                if results["pdf_path"] and os.path.exists(results["pdf_path"]):
                    with open(results["pdf_path"], "rb") as file:
                        pdf_data = file.read()

                    # Provide download button
                    st.download_button(
                        "📥 Download Storybook",
                        data=pdf_data,
                        file_name=f"{character_name}_storybook.pdf",
                        mime="application/pdf",
                    )
            else:
                st.error(f"❌ Failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
