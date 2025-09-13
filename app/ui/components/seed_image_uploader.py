"""Seed image upload component with automatic character reference generation."""

import streamlit as st
from typing import Optional
from google import genai
from app.utils.schemas import StoryMetadata, ArtStyle
from app.utils.settings import settings
from app.ai.image_generator import ImageGenerator
import os


class SeedImageUploader:
    """Image uploader that generates character reference from uploaded photos."""

    @staticmethod
    def render() -> Optional[dict]:
        """Render seed image upload interface with auto-generation.

        Returns:
            Dictionary containing generated seed image and metadata, or None if no data.
        """
        uploaded_files = st.file_uploader(
            "Upload character photos",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Upload photos to generate a character reference image"
        )

        if "generated_character_ref" not in st.session_state:
            st.session_state.generated_character_ref = None

        # Always show character parameters form
        st.divider()
        st.subheader("Character Parameters")

        col1, col2 = st.columns(2)

        with col1:
            character_name = st.text_input("Character Name", value="Hero", key="char_name")
            character_age = st.number_input("Character Age", min_value=1, max_value=18, value=5, key="char_age")

        with col2:
            character_gender = st.selectbox("Gender", ["boy", "girl"], key="char_gender")
            art_style = st.selectbox(
                "Art Style",
                options=[style.value for style in ArtStyle],
                index=0,
                key="art_style"
            )

        system_prompt = st.text_area(
            "System Prompt (Optional)",
            placeholder="Additional character details, themes, mood, or specific requirements for the story",
            height=100,
            key="system_prompt_seed"
        )

        # Generate button if photos are uploaded
        if uploaded_files:
            st.write(f"**Uploaded {len(uploaded_files)} photo(s)**")

            # Generate or regenerate button
            button_text = "Regenerate Character Reference" if st.session_state.generated_character_ref else "Generate Character Reference"

            if st.button(button_text, type="primary", use_container_width=True):
                with st.spinner("Generating character reference..."):
                    try:
                        client = genai.Client(api_key=settings.google_api_key)
                        generator = ImageGenerator(client, settings.model)

                        # Generate character reference using the template
                        image_path = generator.generate_character_reference(
                            character_images=uploaded_files,
                            character_name=character_name,
                            character_age=character_age,
                            character_gender=character_gender,
                            character_info=system_prompt if system_prompt else f"{character_age} year old {character_gender}",
                            art_style=art_style
                        )

                        if image_path:
                            st.session_state.generated_character_ref = image_path
                            st.success("Character reference generated!")
                            st.rerun()
                        else:
                            st.error("Failed to generate character reference")
                    except Exception as e:
                        st.error(f"Error generating character reference: {str(e)}")

        # Display generated character reference
        if st.session_state.generated_character_ref and os.path.exists(st.session_state.generated_character_ref):
            st.divider()
            st.write("**Generated Character Reference:**")
            st.image(st.session_state.generated_character_ref, use_container_width=True)

            st.info("You can regenerate with different parameters or continue to the next step.")

        # Prepare metadata
        metadata = StoryMetadata(
            instructions=system_prompt if system_prompt else None,
            art_style=ArtStyle(art_style)
        )

        # Return the generated character reference as seed image if it exists
        if st.session_state.generated_character_ref:
            return {
                "images": [st.session_state.generated_character_ref],
                "metadata": metadata
            }

        # Return just metadata if no seed image yet
        if system_prompt or uploaded_files:
            return {
                "images": [],
                "metadata": metadata
            }

        return None