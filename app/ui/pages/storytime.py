"""Simplified StoryTime Application.

Single-page workflow for generating AI-powered storybooks:
1. Optional seed image upload with metadata
2. Load and edit story template
3. Generate and edit story content
"""

import streamlit as st
import json
from pathlib import Path

from app.ui.components.seed_image_uploader import SeedImageUploader
from app.ui.components.template_editor import TemplateEditor
from app.ui.components.story_editor import StoryEditor
from app.ai.story_processor import StoryProcessor
from app.utils.schemas import StoryTemplate, SessionStateKeys


def initialize_session_state() -> None:
    defaults = {
        SessionStateKeys.SEED_IMAGES: [],
        SessionStateKeys.METADATA: None,
        SessionStateKeys.STORY_TEMPLATE: None,
        SessionStateKeys.EDITED_TEMPLATE: None,
        SessionStateKeys.GENERATED_PAGES: [],
        SessionStateKeys.SYSTEM_PROMPT: "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_story_templates() -> dict[str, StoryTemplate]:
    templates = {}
    template_dir = Path("app/story_templates")

    if template_dir.exists():
        for template_file in template_dir.glob("*.json"):
            try:
                with open(template_file, "r") as f:
                    data = json.load(f)
                    templates[template_file.stem] = StoryTemplate(
                        name=data.get("name", template_file.stem),
                        description=data.get("description", ""),
                        default_title=data.get("default_title", "Story"),
                        pages=data.get("pages", []),
                    )
            except Exception as e:
                st.error(f"Error loading {template_file.name}: {str(e)}")

    return templates


def render_seed_images_step() -> None:
    st.header("Step 1: Upload Seed Images (Optional)")
    st.write("Upload images to use as visual references for your story.")

    seed_data = SeedImageUploader.render()

    if seed_data:
        st.session_state[SessionStateKeys.SEED_IMAGES] = seed_data.get("images", [])
        st.session_state[SessionStateKeys.METADATA] = seed_data.get("metadata")


def render_story_template_step() -> None:
    """Render Step 2: Load and edit story template."""
    st.header("Step 2: Load and Edit Story Template")

    templates = load_story_templates()

    if not templates:
        st.error("No story templates found in app/story_templates/")
        return

    # Template selection
    template_names = list(templates.keys())
    selected_template_name = st.selectbox(
        "Select a story template",
        template_names,
        help="Choose a pre-defined story structure to edit",
    )

    if selected_template_name:
        if (
            not st.session_state[SessionStateKeys.STORY_TEMPLATE]
            or st.session_state[SessionStateKeys.STORY_TEMPLATE].name
            != templates[selected_template_name].name
        ):
            st.session_state[SessionStateKeys.STORY_TEMPLATE] = templates[
                selected_template_name
            ]
            st.session_state[SessionStateKeys.EDITED_TEMPLATE] = templates[
                selected_template_name
            ]

        st.divider()
        edited_template = TemplateEditor.render(
            st.session_state[SessionStateKeys.EDITED_TEMPLATE]
        )
        st.session_state[SessionStateKeys.EDITED_TEMPLATE] = edited_template


def render_generation_step() -> None:
    """Render Step 3: Story generation and editing."""
    st.header("Step 3: Generate and Edit Story")

    if not st.session_state[SessionStateKeys.EDITED_TEMPLATE]:
        st.warning("Please select and edit a story template first.")
        return

    (col1,) = st.columns(1)

    with col1:
        system_prompt = st.text_area(
            "System Prompt (Optional)",
            value=st.session_state[SessionStateKeys.SYSTEM_PROMPT],
            height=100,
            help="Additional instructions for the AI generation process",
        )
        st.session_state[SessionStateKeys.SYSTEM_PROMPT] = system_prompt

        if st.button("Generate Story", type="primary", width="stretch"):
            with st.spinner("Generating your story..."):
                try:
                    processor = StoryProcessor()
                    # Try to get from widget keys
                    character_name = st.session_state.get(
                        SessionStateKeys.CHAR_NAME, "Hero"
                    )
                    character_age = st.session_state.get(SessionStateKeys.CHAR_AGE, 5)
                    character_gender = st.session_state.get(
                        SessionStateKeys.CHAR_GENDER, "child"
                    )

                    generated_pages = processor.generate_story(
                        story_template=st.session_state[
                            SessionStateKeys.EDITED_TEMPLATE
                        ],
                        seed_images=st.session_state[SessionStateKeys.SEED_IMAGES],
                        metadata=st.session_state[SessionStateKeys.METADATA],
                        system_prompt=system_prompt,
                        character_name=character_name,
                        character_age=character_age,
                        character_gender=character_gender,
                    )

                    if generated_pages:
                        st.session_state[SessionStateKeys.GENERATED_PAGES] = (
                            generated_pages
                        )
                        st.success("Story generated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to generate story. Please try again.")

                except Exception as e:
                    st.error(f"Error generating story: {str(e)}")

    if st.session_state[SessionStateKeys.GENERATED_PAGES]:
        st.divider()
        updated_pages = StoryEditor.render(
            st.session_state[SessionStateKeys.GENERATED_PAGES]
        )
        st.session_state[SessionStateKeys.GENERATED_PAGES] = updated_pages

        if st.button("Regenerate Story", width="stretch"):
            st.session_state[SessionStateKeys.GENERATED_PAGES] = []
            st.rerun()


def main() -> None:
    initialize_session_state()
    render_seed_images_step()
    st.divider()
    render_story_template_step()
    st.divider()
    render_generation_step()


if __name__ == "__main__":
    main()
