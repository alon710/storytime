"""Seed image upload component with automatic character reference generation."""

import streamlit as st
from typing import Optional
from google import genai
from app.utils.schemas import StoryMetadata, ArtStyle
from app.utils.settings import settings
from app.ai.image_generator import ImageGenerator
import os


class SeedImageUploader:
    """Image uploader that supports both direct reference upload and generation from photos."""

    @staticmethod
    def render() -> Optional[dict]:
        """Render seed image upload interface with both upload and generation options.

        Returns:
            Dictionary containing seed image and metadata, or None if no data.
        """
        if "generated_character_ref" not in st.session_state:
            st.session_state.generated_character_ref = None
        if "uploaded_reference" not in st.session_state:
            st.session_state.uploaded_reference = None

        # Choose method: upload reference directly or generate from photos
        st.subheader("Character Reference")

        reference_method = st.radio(
            "Choose how to provide character reference:",
            ["Upload Reference Image", "Generate from Photos"],
            help="Either upload an existing character reference or generate one from photos",
        )

        # Always show character parameters form
        st.divider()
        st.subheader("Character Parameters")

        col1, col2 = st.columns(2)

        with col1:
            character_name = st.text_input(
                "Character Name", value="Hero", key="char_name"
            )
            character_age = st.number_input(
                "Character Age", min_value=1, max_value=18, value=5, key="char_age"
            )

        with col2:
            character_gender = st.selectbox(
                "Gender", ["boy", "girl"], key="char_gender"
            )
            art_style = st.selectbox(
                "Art Style",
                options=[style.value for style in ArtStyle],
                index=0,
                key="art_style",
            )

        system_prompt = st.text_area(
            "System Prompt (Optional)",
            placeholder="Additional character details, themes, mood, or specific requirements for the story",
            height=100,
            key="system_prompt_seed",
        )

        st.divider()

        if reference_method == "Upload Reference Image":
            # Direct reference image upload
            uploaded_reference = st.file_uploader(
                "Upload character reference image",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=False,
                help="Upload a character reference image to use for story generation",
            )

            if uploaded_reference:
                st.session_state.uploaded_reference = uploaded_reference
                st.write("**Uploaded Reference Image:**")
                st.image(uploaded_reference, width="stretch")

                # Clear generated reference if user uploads their own
                st.session_state.generated_character_ref = None

        else:  # Generate from Photos
            uploaded_files = st.file_uploader(
                "Upload character photos",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                help="Upload photos to generate a character reference image",
            )

            if uploaded_files:
                st.write(f"**Uploaded {len(uploaded_files)} photo(s)**")

                # Generate or regenerate button
                button_text = (
                    "Regenerate Character Reference"
                    if st.session_state.generated_character_ref
                    else "Generate Character Reference"
                )

                if st.button(button_text, type="primary", width="stretch"):
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
                                character_info=system_prompt
                                if system_prompt
                                else f"{character_age} year old {character_gender}",
                                art_style=art_style,
                            )

                            if image_path:
                                st.session_state.generated_character_ref = image_path
                                # Clear uploaded reference when generating new one
                                st.session_state.uploaded_reference = None
                                st.success("Character reference generated!")
                                st.rerun()
                            else:
                                st.error("Failed to generate character reference")
                        except Exception as e:
                            st.error(f"Error generating character reference: {str(e)}")

            # Display generated character reference
            if st.session_state.generated_character_ref and os.path.exists(
                st.session_state.generated_character_ref
            ):
                st.divider()
                st.image(st.session_state.generated_character_ref)

        # Prepare metadata
        metadata = StoryMetadata(
            instructions=system_prompt if system_prompt else None,
            art_style=ArtStyle(art_style),
        )

        # Determine which reference to use
        final_reference = None

        if st.session_state.uploaded_reference:
            # Use uploaded reference
            final_reference = [st.session_state.uploaded_reference]
        elif st.session_state.generated_character_ref:
            # Use generated reference
            final_reference = [st.session_state.generated_character_ref]

        # Return the reference image as seed
        if final_reference:
            return {"images": final_reference, "metadata": metadata}

        # Return just metadata if no reference yet but has system prompt
        if system_prompt:
            return {"images": [], "metadata": metadata}

        return None
