import streamlit as st
import os
import json
from app.ai.story_processor import StoryProcessor
from app.utils.settings import settings
from app.utils.schemas import PageData, GeneratedPage


def convert_dict_to_pagedata(page_dict: dict) -> PageData:
    """Convert a dictionary to PageData object."""
    return PageData(
        title=page_dict.get("title", ""),
        story_text=page_dict.get("story_text", ""),
        illustration_prompt=page_dict.get("illustration_prompt", ""),
    )


def convert_pagedata_to_dict(page_data: PageData) -> dict:
    """Convert PageData object to dictionary for session state."""
    return {
        "title": page_data.title,
        "story_text": page_data.story_text,
        "illustration_prompt": page_data.illustration_prompt,
    }


def load_story_templates():
    """Load all JSON templates from story_templates directory"""
    templates = {}
    template_dir = "app/story_templates"

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

    if "generated_pages" not in st.session_state:
        st.session_state.generated_pages = []

    if "preview_complete" not in st.session_state:
        st.session_state.preview_complete = False

    # Story Template Selection
    st.header("Story Template (Optional)")
    templates = load_story_templates()

    if templates:
        template_options = ["Start from scratch"] + [
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
            else:
                # Template selected - load it
                selected_template_key = template_keys[selected_index]
                selected_template = templates[selected_template_key]
                st.session_state.pages = selected_template["pages"]

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
    (col1,) = st.columns(1)

    with col1:
        character_name = st.text_input("Character Name", value="Alex")
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
        if st.button("+ Add Page", width="stretch"):
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
            st.button("- Remove Page", width="stretch")
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

    # Check if we have required inputs
    has_required_inputs = (
        st.session_state.pages
        and character_images
        and character_name
        and character_age
        and character_gender
    )

    # Step 1: Generate Preview
    if not st.session_state.preview_complete and has_required_inputs:
        if st.button("Generate Preview with Images", type="primary", width="stretch"):
            with st.spinner("Generating preview..."):
                processor = StoryProcessor()
                progress_bar = st.progress(0)

                pages_data = [
                    convert_dict_to_pagedata(page_dict=page)
                    for page in st.session_state.pages
                ]

                generated_pages = processor.generate_preview(
                    pages_data=pages_data,
                    character_images=character_images,
                    character_name=character_name,
                    character_age=character_age,
                    character_gender=character_gender,
                    progress_bar=progress_bar,
                )

                if generated_pages:
                    st.session_state.generated_pages = generated_pages
                    st.session_state.preview_complete = True
                    st.success(
                        "Preview generated! You can now edit the text and create your PDF."
                    )
                    st.rerun()
                else:
                    st.error("Failed to generate preview")

    # Step 2: Preview and Edit Interface
    if st.session_state.preview_complete and st.session_state.generated_pages:
        st.header("📖 Preview & Edit Your Storybook")
        st.write(
            "Review the generated images and text. You can edit the text before creating your final PDF."
        )

        for i, generated_page in enumerate(st.session_state.generated_pages):
            with st.expander(
                f"Page {i + 1}: {generated_page.page_data.title}", expanded=True
            ):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.subheader("Generated Image")
                    if generated_page.image_path and os.path.exists(
                        generated_page.image_path
                    ):
                        st.image(generated_page.image_path, width="stretch")
                    else:
                        st.error("Image not found")

                with col2:
                    st.subheader("Story Text")
                    # Show editable text area
                    current_text = (
                        generated_page.edited_text
                        if generated_page.edited_text
                        else generated_page.personalized_text
                    )

                    edited_text = st.text_area(
                        f"Edit text for page {i + 1}",
                        value=current_text,
                        height=150,
                        key=f"edit_text_{i}",
                        help="Edit this text as needed. This will appear in your final PDF.",
                    )

                    # Update the generated page with edited text if changed
                    if edited_text != current_text:
                        st.session_state.generated_pages[i].edited_text = edited_text

        st.divider()

        # Step 3: Create Final PDF
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Regenerate Preview", width="stretch"):
                st.session_state.preview_complete = False
                st.session_state.generated_pages = []
                st.rerun()

        with col2:
            if st.button("📄 Create Final PDF", type="primary", width="stretch"):
                with st.spinner("Creating your personalized storybook PDF..."):
                    processor = StoryProcessor()

                    pdf_path = processor.create_pdf_from_preview(
                        generated_pages=st.session_state.generated_pages,
                        character_name=character_name,
                        character_age=character_age,
                        character_gender=character_gender,
                    )

                    if pdf_path and os.path.exists(pdf_path):
                        st.success("🎉 Your personalized storybook is ready!")

                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                "📥 Download Your Storybook PDF",
                                data=pdf_file.read(),
                                file_name=f"{character_name}_storybook.pdf",
                                mime="application/pdf",
                                width="stretch",
                            )
                    else:
                        st.error("Failed to create PDF")

    elif not has_required_inputs:
        st.info(
            "👆 Please fill in all story pages, upload character photos, and complete book settings before generating your preview."
        )


main()
