"""Template editor component for editing loaded story templates."""

import streamlit as st
from app.utils.schemas import PageData, StoryTemplate


class TemplateEditor:
    @staticmethod
    def render(template: StoryTemplate) -> StoryTemplate:
        st.subheader("Edit Story Template")

        (col1,) = st.columns(1)
        with col1:
            template.default_title = st.text_input(
                "Story Title",
                value=template.default_title,
                key="template_title",
            )
            template.description = st.text_area(
                "Description",
                value=template.description,
                key="template_description",
            )

        st.divider()
        st.write(f"**Pages ({len(template.pages)})**")

        updated_pages = []

        for i, page in enumerate(template.pages):
            with st.container():
                header_col1, header_col2 = st.columns([0.95, 0.05])
                with header_col1:
                    st.write(f"**Page {i + 1}**")
                with header_col2:
                    if st.button(
                        "❌",
                        key=f"remove_template_page_{i}",
                        help="Remove this page",
                        type="tertiary",
                    ):
                        # Skip this page and trigger rerun
                        template.pages = [
                            p for j, p in enumerate(template.pages) if j != i
                        ]
                        st.rerun()

                # Edit page fields
                page.title = st.text_input(
                    "Page Title", value=page.title, key=f"template_page_title_{i}"
                )

                (col1,) = st.columns(1)

                with col1:
                    page.story_text = st.text_area(
                        "Story Text",
                        value=page.story_text,
                        height=100,
                        key=f"template_story_text_{i}",
                        help="The narrative text for this page",
                    )

                    page.illustration_prompt = st.text_area(
                        "Illustration Prompt",
                        value=page.illustration_prompt,
                        height=100,
                        key=f"template_illustration_{i}",
                        help="Description of the illustration to generate",
                    )

                updated_pages.append(page)

        # Add new page button
        if st.button("Add New Page", key="add_template_page"):
            new_page = PageData(
                title=f"Page {len(template.pages) + 1}",
                story_text="Enter story text here...",
                illustration_prompt="Describe the illustration...",
            )
            template.pages.append(new_page)
            st.rerun()

        # Update template with current pages
        template.pages = updated_pages

        return template
