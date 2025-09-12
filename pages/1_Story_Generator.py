"""
StoryTime Story Generator Page
Create custom illustrated PDF storybooks with dynamic page creation
"""

import streamlit as st
import os
import json
from pathlib import Path
from story_processor import StoryProcessor
from config import settings


def load_story_templates():
    """Load all JSON templates from story_templates directory"""
    templates = {}
    template_dir = "story_templates"

    if os.path.exists(template_dir):
        for filename in os.listdir(template_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(template_dir, filename), "r") as f:
                        template_key = filename.replace(".json", "")
                        templates[template_key] = json.load(f)
                except Exception as e:
                    st.error(f"Error loading template {filename}: {str(e)}")

    return templates


def main():
    """Story Generator page with dynamic page creation interface"""

    try:
        settings.google_api_key
    except Exception:
        st.error("Warning: Please set your GOOGLE_API_KEY in your .env file")
        st.info("You can get an API key from: https://makersuite.google.com/app/apikey")
        st.stop()

    if "pages" not in st.session_state:
        st.session_state.pages = []

    # Story Template Selection
    st.header("Story Template (Optional)")
    templates = load_story_templates()

    if templates:
        template_options = ["None - Start from scratch"] + [
            template["name"] for template in templates.values()
        ]
        template_keys = ["none"] + list(templates.keys())

        # Get current selection from session state, default to 0
        current_selection = st.session_state.get("template_selection", 0)

        selected_index = st.selectbox(
            "Choose a template to start with:",
            options=range(len(template_options)),
            format_func=lambda x: template_options[x],
            index=current_selection,
            help="Select a pre-made story structure or start from scratch",
        )

        # Check if selection changed
        if selected_index != current_selection:
            st.session_state.template_selection = selected_index

            if selected_index == 0:
                # "None" selected - clear pages
                st.session_state.pages = []
                st.session_state.book_title = "My Adventure"
            else:
                # Template selected - load it
                selected_template_key = template_keys[selected_index]
                selected_template = templates[selected_template_key]
                st.session_state.pages = selected_template["pages"]
                st.session_state.book_title = selected_template.get(
                    "default_title", "My Adventure"
                )

            st.rerun()

        # Show description for selected template
        if selected_index > 0:
            selected_template_key = template_keys[selected_index]
            selected_template = templates[selected_template_key]
    else:
        st.info(
            "No story templates found. You can start creating your story from scratch."
        )

    st.divider()

    st.header("Book Settings")
    col1, col2 = st.columns(2)

    with col1:
        # Use session state book title if it exists (from template), otherwise default
        default_book_title = st.session_state.get("book_title", "My Adventure")
        book_title = st.text_input("Book Title", value=default_book_title)
        character_name = st.text_input("Character Name", value="Alex")

    with col2:
        character_gender = st.selectbox("Gender", ["Girl", "Boy"])
        character_age = st.number_input("Age", min_value=1, max_value=12, value=5)

    character_images = st.file_uploader(
        "Upload Character Photos (up to 3)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Upload 1-3 photos of the child for character reference",
    )

    # Add validation for image count
    if character_images and len(character_images) > 3:
        st.error("Please upload a maximum of 3 photos.")
        st.stop()
    st.divider()

    st.header("Story Pages")

    (col1, col2) = st.columns(2)
    with col1:
        if st.button("+ Add Page", use_container_width=True):
            page_num = len(st.session_state.pages) + 1
            st.session_state.pages.append(
                {
                    "title": f"Page {page_num}",
                    "story_text": "",
                    "illustration_prompt": "",
                }
            )
            st.rerun()
    with col2:
        if (
            st.button("- Remove Page", use_container_width=True)
            and len(st.session_state.pages) > 1
        ):
            st.session_state.pages.pop()
            st.rerun()

    # Show message when no pages exist
    if not st.session_state.pages:
        st.info(
            "📖 No story pages yet. Click '+ Add Page' to start creating your story, or load a template above."
        )

    for i, page in enumerate(st.session_state.pages):
        with st.expander(f"Page: {page['title']}", expanded=True):
            (col1,) = st.columns(1)

            with col1:
                new_title = st.text_input(
                    "Page Title", value=page["title"], key=f"title_{i}"
                )
                new_story_text = st.text_area(
                    "Story Text (for context)",
                    value=page["story_text"],
                    height=100,
                    help="This text provides context but won't appear in the final PDF",
                    key=f"story_{i}",
                )

                new_illustration_prompt = st.text_area(
                    "Illustration Prompt",
                    value=page["illustration_prompt"],
                    height=140,
                    help="Describe what you want to see in the illustration for this page",
                    key=f"prompt_{i}",
                )

            st.session_state.pages[i] = {
                "title": new_title,
                "story_text": new_story_text,
                "illustration_prompt": new_illustration_prompt,
            }

    st.divider()

    if st.button(
        "Generate Illustrated Storybook", type="primary", use_container_width=True
    ):
        missing_fields = []
        if not character_images:
            missing_fields.append("Character Photos")
        if not character_name.strip():
            missing_fields.append("Character Name")
        if not book_title.strip():
            missing_fields.append("Book Title")

        empty_prompts = []
        for i, page in enumerate(st.session_state.pages):
            if not page["illustration_prompt"].strip():
                empty_prompts.append(f"Page {i + 1}")

        if missing_fields:
            st.error(f"Please provide: {', '.join(missing_fields)}")
        elif empty_prompts:
            st.error(f"Please add illustration prompts for: {', '.join(empty_prompts)}")
        else:
            output_path = Path.cwd()

            with st.spinner("Creating your illustrated storybook..."):
                processor = StoryProcessor()
                progress_bar = st.progress(0)

                results = processor.process_story(
                    pages_data=st.session_state.pages,
                    character_images=character_images,
                    character_name=character_name,
                    character_age=character_age,
                    character_gender=character_gender,
                    book_title=book_title,
                    output_folder=str(output_path),
                    progress_bar=progress_bar,
                )

                if results["success"]:
                    st.success("Illustrated storybook created successfully!")
                    if results["pdf_path"] and os.path.exists(results["pdf_path"]):
                        with open(results["pdf_path"], "rb") as pdf_file:
                            st.download_button(
                                "Download PDF",
                                data=pdf_file.read(),
                                file_name=f"{book_title.replace(' ', '_')}_storybook.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )

                        st.info(
                            f"Generated {results['pages_processed']} illustrations in {results['processing_time']:.1f} seconds"
                        )
                else:
                    st.error(f"Failed: {results.get('error', 'Unknown error')}")


main()
