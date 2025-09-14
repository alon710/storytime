"""Dynamic story editor component for viewing and editing generated content."""

import streamlit as st
import os
from typing import List
from app.utils.schemas import GeneratedPage


class StoryEditor:
    @staticmethod
    def render(generated_pages: List[GeneratedPage]) -> List[GeneratedPage]:
        if not generated_pages:
            return generated_pages

        st.subheader("Story Preview and Editor")

        updated_pages = []

        for i, page in enumerate(generated_pages):
            with st.container():
                (header_col1, _) = st.columns([10, 1])
                with header_col1:
                    st.write(f"**Page {page.page_number}: {page.title}**")

                img_col, text_col = st.columns([1, 1])

                with img_col:
                    if page.image_path and os.path.exists(page.image_path):
                        st.image(page.image_path, width="stretch")
                    else:
                        st.info("No image generated")

                with text_col:
                    current_text = page.edited_text if page.edited_text else page.text
                    edited_text = st.text_area(
                        "Story Text",
                        value=current_text,
                        height=200,
                        key=f"text_edit_{i}",
                        label_visibility="collapsed",
                    )

                    if edited_text != current_text:
                        page.edited_text = edited_text

                updated_pages.append(page)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Add New Page", use_container_width=True):
                new_page_number = len(generated_pages) + 1
                new_page = GeneratedPage(
                    page_number=new_page_number,
                    title=f"New Page {new_page_number}",
                    text="Enter your story text here...",
                    illustration_prompt="Describe the illustration for this page",
                    image_path=None,
                )
                generated_pages.append(new_page)
                st.rerun()

        with col2:
            if st.button(
                "Save All Changes",
                use_container_width=True,
            ):
                st.rerun()

        return updated_pages
