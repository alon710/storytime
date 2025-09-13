"""Dynamic story editor component for viewing and editing generated content."""

import streamlit as st
import os
from typing import List
from app.utils.schemas import GeneratedPage


class StoryEditor:
    """Dynamic editor for story pages with inline text editing and page management."""

    @staticmethod
    def render(generated_pages: List[GeneratedPage]) -> List[GeneratedPage]:
        """Render the story editor interface.

        Args:
            generated_pages: List of GeneratedPage objects

        Returns:
            Updated list of GeneratedPage objects with edits applied
        """
        if not generated_pages:
            st.info("No pages generated yet. Click 'Generate Story' to begin.")
            return generated_pages

        st.subheader("Story Preview and Editor")

        # Page management controls
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"Total Pages: {len(generated_pages)}")

        updated_pages = []
        pages_to_remove = []

        for i, page in enumerate(generated_pages):
            with st.container():
                # Page header with remove button
                header_col1, header_col2 = st.columns([10, 1])
                with header_col1:
                    st.write(f"**Page {page.page_number}: {page.title}**")
                with header_col2:
                    if st.button("✕", key=f"remove_page_{i}", help="Remove this page"):
                        pages_to_remove.append(i)
                        continue

                # Content columns
                img_col, text_col = st.columns([1, 1])

                with img_col:
                    if page.image_path and os.path.exists(page.image_path):
                        st.image(page.image_path, use_container_width=True)
                    else:
                        st.info("No image generated")

                with text_col:
                    # Editable text
                    current_text = page.edited_text if page.edited_text else page.text
                    edited_text = st.text_area(
                        "Story Text",
                        value=current_text,
                        height=200,
                        key=f"text_edit_{i}",
                        label_visibility="collapsed"
                    )

                    # Update edited text if changed
                    if edited_text != current_text:
                        page.edited_text = edited_text

                    # Show illustration prompt
                    with st.expander("Illustration Prompt"):
                        st.text(page.illustration_prompt)

                st.divider()

                # Add page to updated list if not marked for removal
                if i not in pages_to_remove:
                    updated_pages.append(page)

        # Add new page button
        if st.button("Add New Page", use_container_width=True):
            new_page_number = len(updated_pages) + 1
            new_page = GeneratedPage(
                page_number=new_page_number,
                title=f"New Page {new_page_number}",
                text="Enter your story text here...",
                illustration_prompt="Describe the illustration for this page",
                image_path=None
            )
            updated_pages.append(new_page)
            st.rerun()

        # Re-number pages after any removals
        for i, page in enumerate(updated_pages):
            page.page_number = i + 1

        return updated_pages