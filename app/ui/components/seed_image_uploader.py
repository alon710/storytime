import streamlit as st
from typing import Optional
from pathlib import Path
from google import genai
from app.utils.schemas import StoryMetadata, ArtStyle, SessionStateKeys, SeedImageData
from app.utils.settings import settings
from app.ai.image_generator import ImageGenerator
from app.utils.schemas import Gender, Language, SeedMethod


class SeedImageUploader:
    @staticmethod
    def initialize_session_state() -> None:
        defaults = {
            SessionStateKeys.GENERATED_CHARACTER_SEED: None,
            SessionStateKeys.UPLOADED_SEED: None,
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def render() -> Optional[SeedImageData]:
        SeedImageUploader.initialize_session_state()

        st.header("Step 1: Story Parameters")
        st.subheader("Character Seed")

        seed_method = st.radio(
            "Choose how to provide character seed",
            options=[method.value for method in SeedMethod],
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
            value=st.session_state.get(SessionStateKeys.SYSTEM_PROMPT, ""),
            height=100,
            help="Additional character details, themes, mood, or specific requirements for the story",
            placeholder="Additional character details, themes, mood, or specific requirements for the story",
            key=SessionStateKeys.SYSTEM_PROMPT,
        )

        st.divider()

        if seed_method == SeedMethod.upload.value:
            uploaded_seed = st.file_uploader(
                "Upload character seed image",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=False,
                help="Upload a character seed image to use for story generation",
            )

            if uploaded_seed:
                st.session_state[SessionStateKeys.UPLOADED_SEED] = uploaded_seed
                st.write("**Uploaded Seed Image:**")
                st.image(uploaded_seed, width="stretch")
                st.session_state[SessionStateKeys.GENERATED_CHARACTER_SEED] = None

        elif seed_method == SeedMethod.generate.value:
            uploaded_files = st.file_uploader(
                "Upload character photos",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                help="Upload photos to generate a character seed image",
            )

            if uploaded_files:
                st.write(f"**Uploaded {len(uploaded_files)} photo(s)**")

                button_text = (
                    "Regenerate Character Seed"
                    if st.session_state[SessionStateKeys.GENERATED_CHARACTER_SEED]
                    else "Generate Character Seed"
                )

                if st.button(button_text, type="primary", width="stretch"):
                    with st.spinner("Generating character seed..."):
                        try:
                            client = genai.Client(api_key=settings.google_api_key)
                            generator = ImageGenerator(client, settings.model)

                            image_path = generator.generate_character_seed(
                                character_images=uploaded_files,
                                character_name=character_name,
                                character_age=character_age,
                                character_gender=character_gender,
                                art_style=art_style,
                                system_prompt=system_prompt,
                            )

                            if image_path:
                                st.session_state[
                                    SessionStateKeys.GENERATED_CHARACTER_SEED
                                ] = image_path
                                st.session_state[SessionStateKeys.UPLOADED_SEED] = None
                                st.success("Character seed generated!")
                                st.rerun()
                            else:
                                st.error("Failed to generate character seed")
                        except Exception as e:
                            st.error(f"Error generating character seed: {str(e)}")

            if (
                st.session_state[SessionStateKeys.GENERATED_CHARACTER_SEED]
                and Path(
                    st.session_state[SessionStateKeys.GENERATED_CHARACTER_SEED]
                ).exists()
            ):
                st.divider()
                st.image(st.session_state[SessionStateKeys.GENERATED_CHARACTER_SEED])

        metadata = StoryMetadata(
            instructions=system_prompt if system_prompt else None,
            art_style=ArtStyle(art_style),
            character_name=character_name if character_name else "Hero",
            age=character_age,
            gender=Gender(character_gender),
            language=language,
        )

        final_seed = None

        if st.session_state[SessionStateKeys.UPLOADED_SEED]:
            final_seed = [st.session_state[SessionStateKeys.UPLOADED_SEED]]
        elif st.session_state[SessionStateKeys.GENERATED_CHARACTER_SEED]:
            final_seed = [st.session_state[SessionStateKeys.GENERATED_CHARACTER_SEED]]

        # Always return SeedImageData with metadata (including system prompt)
        return SeedImageData(images=final_seed or [], metadata=metadata)
