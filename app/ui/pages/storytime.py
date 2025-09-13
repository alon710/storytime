"""Simplified StoryTime Application.

Single-page workflow for generating AI-powered storybooks:
1. Optional seed image upload with metadata
2. Load story template
3. Generate and edit story content
"""

import streamlit as st
import json
from pathlib import Path

from app.ui.components.seed_image_uploader import SeedImageUploader
from app.ui.components.story_editor import StoryEditor
from app.ai.story_processor import StoryProcessor
from app.utils.schemas import StoryTemplate


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "seed_images" not in st.session_state:
        st.session_state.seed_images = []

    if "metadata" not in st.session_state:
        st.session_state.metadata = None

    if "story_template" not in st.session_state:
        st.session_state.story_template = None

    if "generated_pages" not in st.session_state:
        st.session_state.generated_pages = []

    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = ""


def load_story_templates() -> dict[str, StoryTemplate]:
    """Load available story templates from the story_templates directory."""
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
                        pages=data.get("pages", [])
                    )
            except Exception as e:
                st.error(f"Error loading {template_file.name}: {str(e)}")

    return templates


def render_seed_images_step() -> None:
    """Render Step 1: Optional seed image upload."""
    st.header("Step 1: Upload Seed Images (Optional)")
    st.write("Upload images to use as visual references for your story.")

    seed_data = SeedImageUploader.render()

    if seed_data:
        st.session_state.seed_images = seed_data.get("images", [])
        st.session_state.metadata = seed_data.get("metadata")


def render_story_selection_step() -> None:
    """Render Step 2: Story template selection."""
    st.header("Step 2: Load Story Template")

    templates = load_story_templates()

    if not templates:
        st.error("No story templates found in app/story_templates/")
        return

    template_names = list(templates.keys())
    selected_template_name = st.selectbox(
        "Select a story template",
        template_names,
        help="Choose a pre-defined story structure"
    )

    if selected_template_name:
        template = templates[selected_template_name]
        st.session_state.story_template = template

        with st.expander("Template Details", expanded=False):
            st.write(f"**Title:** {template.default_title}")
            st.write(f"**Description:** {template.description}")
            st.write(f"**Pages:** {len(template.pages)}")


def render_generation_step() -> None:
    """Render Step 3: Story generation and editing."""
    st.header("Step 3: Generate and Edit Story")

    if not st.session_state.story_template:
        st.warning("Please select a story template first.")
        return

    col1, col2 = st.columns(2)

    with col1:
        system_prompt = st.text_area(
            "System Prompt (Optional)",
            value=st.session_state.system_prompt,
            height=100,
            help="Additional instructions for the AI generation process"
        )
        st.session_state.system_prompt = system_prompt

    with col2:
        if st.button("Generate Story", type="primary", use_container_width=True):
            with st.spinner("Generating your story..."):
                try:
                    processor = StoryProcessor()

                    generated_pages = processor.generate_story(
                        story_template=st.session_state.story_template,
                        seed_images=st.session_state.seed_images,
                        metadata=st.session_state.metadata,
                        system_prompt=system_prompt
                    )

                    if generated_pages:
                        st.session_state.generated_pages = generated_pages
                        st.success("Story generated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to generate story. Please try again.")

                except Exception as e:
                    st.error(f"Error generating story: {str(e)}")

    if st.session_state.generated_pages:
        st.divider()
        updated_pages = StoryEditor.render(st.session_state.generated_pages)
        st.session_state.generated_pages = updated_pages

        if st.button("Regenerate Story", use_container_width=True):
            st.session_state.generated_pages = []
            st.rerun()


def main() -> None:
    """Main StoryTime application entry point."""
    initialize_session_state()

    render_seed_images_step()

    st.divider()

    render_story_selection_step()

    st.divider()

    render_generation_step()


if __name__ == "__main__":
    main()