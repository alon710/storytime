import streamlit as st
from typing import Optional
from pathlib import Path
from google import genai
from app.utils.schemas import (
    SessionStateKeys,
    SeedImageData,
    ReferenceMethod,
    StoryMetadata,
)
from app.utils.settings import settings
from app.ai.image_generator import ImageGenerator


class SeedImageUploader:
    @staticmethod
    def initialize_session_state() -> None:
        defaults = {
            SessionStateKeys.GENERATED_CHARACTER_REF: None,
            SessionStateKeys.UPLOADED_REFERENCE: None,
            SessionStateKeys.SEED_IMAGES: [],
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def render(metadata: Optional[StoryMetadata] = None) -> Optional[SeedImageData]:
        SeedImageUploader.initialize_session_state()

        st.subheader("Character Reference Image")
        st.write("Provide a visual reference for your story's main character.")

        reference_method = st.radio(
            "Choose how to provide character reference",
            options=[method.value for method in ReferenceMethod],
            horizontal=True,
            help="Upload an existing reference image or generate one from photos",
        )

        st.divider()

        if reference_method == ReferenceMethod.upload.value:
            uploaded_reference = st.file_uploader(
                "Upload character reference image",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=False,
                help="Upload a character reference image to use for story generation",
            )

            if uploaded_reference:
                st.session_state[SessionStateKeys.UPLOADED_REFERENCE] = (
                    uploaded_reference
                )
                st.write("**Uploaded Reference Image:**")
                st.image(uploaded_reference, width="stretch")
                st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF] = None

        elif reference_method == ReferenceMethod.generate.value:
            uploaded_files = st.file_uploader(
                "Upload character photos",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                help="Upload photos to generate a character reference image",
            )

            if uploaded_files and metadata:
                st.write(f"**Uploaded {len(uploaded_files)} photo(s)**")

                st.info(
                    f"Character: {metadata.character_name}, Age: {metadata.age}, Gender: {metadata.gender.value}"
                )

                button_text = (
                    "Regenerate Character Reference"
                    if st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]
                    else "Generate Character Reference"
                )

                if st.button(button_text, use_container_width=True):
                    with st.spinner("Generating character reference..."):
                        try:
                            client = genai.Client(api_key=settings.google_api_key)
                            generator = ImageGenerator(client, settings.model)

                            image_path = generator.generate_character_reference(
                                character_images=uploaded_files,
                                character_name=metadata.character_name,
                                character_age=metadata.age,
                                character_gender=metadata.gender.value,
                                art_style=metadata.art_style.value,
                                system_prompt=metadata.instructions or "",
                            )

                            if image_path:
                                st.session_state[
                                    SessionStateKeys.GENERATED_CHARACTER_REF
                                ] = image_path
                                st.session_state[
                                    SessionStateKeys.UPLOADED_REFERENCE
                                ] = None
                                st.success("Character reference generated!")
                                st.rerun()
                            else:
                                st.error("Failed to generate character reference")
                        except Exception as e:
                            st.error(f"Error generating character reference: {str(e)}")
            elif uploaded_files and not metadata:
                st.warning(
                    "Please configure story metadata first (Step 1) before generating character reference."
                )

            if (
                st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]
                and Path(
                    st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]
                ).exists()
            ):
                st.divider()
                st.write("**Generated Character Reference:**")
                st.image(st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF])

        final_reference = None

        if st.session_state[SessionStateKeys.UPLOADED_REFERENCE]:
            final_reference = [st.session_state[SessionStateKeys.UPLOADED_REFERENCE]]
        elif st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]:
            final_reference = [
                st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]
            ]

        if final_reference:
            st.session_state[SessionStateKeys.SEED_IMAGES] = final_reference
            return SeedImageData(images=final_reference, metadata=metadata)

        return None
