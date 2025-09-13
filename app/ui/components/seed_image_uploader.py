"""Seed image upload component with metadata input."""

import streamlit as st
from typing import Optional
from app.utils.schemas import StoryMetadata, ArtStyle


class SeedImageUploader:
    """Simple image uploader with metadata for story generation."""

    @staticmethod
    def render() -> Optional[dict]:
        """Render seed image upload interface.

        Returns:
            Dictionary containing uploaded images and metadata, or None if no data.
        """
        uploaded_files = st.file_uploader(
            "Upload seed images",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Upload images to use as visual references for story generation"
        )

        metadata = None

        if uploaded_files:
            st.write(f"Uploaded {len(uploaded_files)} image(s)")

            with st.expander("Story Metadata (Optional)", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    title = st.text_input("Story Title", placeholder="Optional custom title")
                    art_style = st.selectbox(
                        "Art Style",
                        options=[style.value for style in ArtStyle],
                        index=0
                    )

                with col2:
                    description = st.text_input(
                        "Description",
                        placeholder="Brief story description"
                    )

                instructions = st.text_area(
                    "Instructions",
                    placeholder="Free-text instructions for AI generation (e.g., character details, themes, mood)",
                    height=100
                )

                additional_context = st.text_area(
                    "Additional Context",
                    placeholder="Any other context or requirements",
                    height=80
                )

                metadata = StoryMetadata(
                    title=title if title else None,
                    description=description if description else None,
                    instructions=instructions if instructions else None,
                    art_style=ArtStyle(art_style),
                    additional_context=additional_context if additional_context else None
                )

            return {
                "images": uploaded_files,
                "metadata": metadata
            }

        return None