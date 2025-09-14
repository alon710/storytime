import streamlit as st
from typing import Optional
from pathlib import Path
from google import genai
from app.utils.schemas import StoryMetadata, ArtStyle, SessionStateKeys, SeedImageData
from app.utils.settings import settings
from app.ai.image_generator import ImageGenerator
from app.utils.schemas import Gender, Language, ReferenceMethod


class SeedImageUploader:
    @staticmethod
    def initialize_session_state() -> None:
        defaults = {
            SessionStateKeys.GENERATED_CHARACTER_REF: None,
            SessionStateKeys.UPLOADED_REFERENCE: None,
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def render() -> Optional[SeedImageData]:
        SeedImageUploader.initialize_session_state()

        st.subheader("Character Reference")

        reference_method = st.radio(
            "Choose how to provide character reference",
            options=[method.value for method in ReferenceMethod],
            horizontal=True,
        )

        st.divider()
        st.subheader("Character Parameters")

        col1, col2 = st.columns(2)

        with col1:
            character_name = st.text_input(
                "Character Name",
                placeholder="e.g., Alice, Tom",
                key=SessionStateKeys.CHAR_NAME,
            )
            character_age = st.number_input(
                "Character Age",
                min_value=1,
                max_value=18,
                key=SessionStateKeys.CHAR_AGE,
            )

        with col2:
            character_gender = st.selectbox(
                "Gender",
                options=[gender.value for gender in Gender],
                key=SessionStateKeys.CHAR_GENDER,
            )
            art_style = st.selectbox(
                "Art Style",
                options=[style.value for style in ArtStyle],
                index=0,
                key=SessionStateKeys.ART_STYLE,
            )

        (col3,) = st.columns(1)
        with col3:
            language = st.selectbox(
                "Language",
                options=[lang.value for lang in Language],
                key=SessionStateKeys.LANGUAGE,
            )

        system_prompt = st.text_area(
            "System Prompt (Optional)",
            placeholder="Additional character details, themes, mood, or specific requirements for the story",
            height=100,
            key=SessionStateKeys.SYSTEM_PROMPT_SEED,
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

            if uploaded_files:
                st.write(f"**Uploaded {len(uploaded_files)} photo(s)**")

                button_text = (
                    "Regenerate Character Reference"
                    if st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]
                    else "Generate Character Reference"
                )

                if st.button(button_text, type="primary", width="stretch"):
                    with st.spinner("Generating character reference..."):
                        try:
                            client = genai.Client(api_key=settings.google_api_key)
                            generator = ImageGenerator(client, settings.model)

                            image_path = generator.generate_character_reference(
                                character_images=uploaded_files,
                                character_name=character_name,
                                character_age=character_age,
                                character_gender=character_gender,
                                art_style=art_style,
                                system_prompt=system_prompt,
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

            if (
                st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]
                and Path(
                    st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]
                ).exists()
            ):
                st.divider()
                st.image(st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF])

        metadata = StoryMetadata(
            instructions=system_prompt if system_prompt else None,
            art_style=ArtStyle(art_style),
            character_name=character_name if character_name else "Hero",
            age=character_age,
            gender=Gender(character_gender),
            language=language,
        )

        final_reference = None

        if st.session_state[SessionStateKeys.UPLOADED_REFERENCE]:
            final_reference = [st.session_state[SessionStateKeys.UPLOADED_REFERENCE]]
        elif st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]:
            final_reference = [
                st.session_state[SessionStateKeys.GENERATED_CHARACTER_REF]
            ]

        if final_reference or system_prompt:
            return SeedImageData(images=final_reference or [], metadata=metadata)

        return None
