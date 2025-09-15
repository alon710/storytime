import streamlit as st
from typing import Optional
from app.utils.schemas import (
    StoryMetadata,
    ArtStyle,
    Gender,
    Language,
    SessionStateKeys,
)


class MetadataManager:
    @staticmethod
    def initialize_session_state() -> None:
        defaults = {
            SessionStateKeys.METADATA: None,
            SessionStateKeys.CHAR_NAME: "Hero",
            SessionStateKeys.CHAR_AGE: 5,
            SessionStateKeys.CHAR_GENDER: Gender.boy.value,
            SessionStateKeys.LANGUAGE: Language.english.value,
            SessionStateKeys.ART_STYLE: ArtStyle.watercolor.value,
            SessionStateKeys.SYSTEM_PROMPT: "",
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def render() -> Optional[StoryMetadata]:
        MetadataManager.initialize_session_state()

        st.subheader("Story Configuration")

        col1, col2 = st.columns(2)

        with col1:
            character_name = st.text_input(
                "Character Name",
                placeholder="e.g., Alice, Tom",
                key=SessionStateKeys.CHAR_NAME,
                help="The main character's name for your story",
            )
            character_age = st.number_input(
                "Character Age",
                min_value=1,
                max_value=18,
                key=SessionStateKeys.CHAR_AGE,
                help="The age of the main character",
            )
            character_gender = st.selectbox(
                "Gender",
                options=[gender.value for gender in Gender],
                key=SessionStateKeys.CHAR_GENDER,
                help="The gender of the main character",
            )

        with col2:
            language = st.selectbox(
                "Story Language",
                options=[lang.value for lang in Language],
                key=SessionStateKeys.LANGUAGE,
                help="The language in which the story will be generated",
            )
            art_style = st.selectbox(
                "Art Style",
                options=[style.value for style in ArtStyle],
                key=SessionStateKeys.ART_STYLE,
                help="The artistic style for story illustrations",
            )

        system_prompt = st.text_area(
            "Story Instructions (Optional)",
            placeholder="Additional character details, themes, mood, or specific requirements for the story",
            height=100,
            key=SessionStateKeys.SYSTEM_PROMPT,
            help="Provide any additional context or requirements for your story",
        )

        metadata = StoryMetadata(
            character_name=character_name or "Hero",
            age=character_age,
            gender=Gender(character_gender),
            language=Language(language),
            art_style=ArtStyle(art_style),
            instructions=system_prompt if system_prompt else None,
        )

        st.session_state[SessionStateKeys.METADATA] = metadata

        return metadata

    @staticmethod
    def get_current_metadata() -> Optional[StoryMetadata]:
        return st.session_state.get(SessionStateKeys.METADATA)

    @staticmethod
    def update_metadata(metadata: StoryMetadata) -> None:
        st.session_state[SessionStateKeys.METADATA] = metadata
        st.session_state[SessionStateKeys.CHAR_NAME] = metadata.character_name
        st.session_state[SessionStateKeys.CHAR_AGE] = metadata.age
        st.session_state[SessionStateKeys.CHAR_GENDER] = metadata.gender.value
        st.session_state[SessionStateKeys.LANGUAGE] = metadata.language
        st.session_state[SessionStateKeys.ART_STYLE] = metadata.art_style.value
        if metadata.instructions:
            st.session_state[SessionStateKeys.SYSTEM_PROMPT] = metadata.instructions
