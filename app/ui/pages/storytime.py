"""Simplified StoryTime Application with Multi-Step Form Workflow.

Three-step workflow for generating AI-powered storybooks:
1. Story Parameters (character seed, settings, template selection)
2. Edit Story Template
3. Generate and Edit Story
"""

import streamlit as st
import json
from pathlib import Path

from app.ui.components.seed_image_uploader import SeedImageUploader
from app.ui.components.template_editor import TemplateEditor
from app.ui.components.story_editor import StoryEditor
from app.ai.story_processor import StoryProcessor
from app.utils.schemas import (
    Gender,
    Language,
    StoryTemplate,
    SessionStateKeys,
    Step,
)
from app.utils.download_manager import DownloadManager


def initialize_session_state() -> None:
    defaults = {
        SessionStateKeys.SEED_IMAGES: [],
        SessionStateKeys.METADATA: None,
        SessionStateKeys.STORY_TEMPLATE: None,
        SessionStateKeys.EDITED_TEMPLATE: None,
        SessionStateKeys.GENERATED_PAGES: [],
        SessionStateKeys.SYSTEM_PROMPT: "",
        SessionStateKeys.STEP: Step.story_parameters,
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


def advance_to_edit_template():
    st.session_state[SessionStateKeys.STEP] = Step.edit_template


def advance_to_generate_story():
    """Transition to the story generation step."""
    st.session_state[SessionStateKeys.STEP] = Step.generate_story


def back_to_edit_template():
    """Go back to the template editing step."""
    st.session_state[SessionStateKeys.STEP] = Step.edit_template


def render_story_parameters_step() -> None:
    seed_data = SeedImageUploader.render()

    if seed_data:
        st.session_state[SessionStateKeys.SEED_IMAGES] = seed_data.images
        st.session_state[SessionStateKeys.METADATA] = seed_data.metadata

    st.divider()
    st.subheader("Story Template")

    templates: dict[str, StoryTemplate] = load_story_templates()

    selected_template_name = st.selectbox(
        "Select a story template",
        options=list(templates.keys()),
        help="Choose a pre-defined story structure to edit",
    )

    if selected_template_name:
        selected_template = templates[selected_template_name]
        st.info(f"**Description:** {selected_template.description}")

        if (
            not st.session_state[SessionStateKeys.STORY_TEMPLATE]
            or st.session_state[SessionStateKeys.STORY_TEMPLATE].name
            != selected_template.name
        ):
            st.session_state[SessionStateKeys.STORY_TEMPLATE] = selected_template
            st.session_state[SessionStateKeys.EDITED_TEMPLATE] = selected_template

    if st.button(
        "Continue to Edit Template",
        use_container_width=True,
    ):
        advance_to_edit_template()
        st.rerun()


def render_edit_template_step() -> None:
    """Step 2: Edit the selected story template."""
    st.header("Step 2: Edit Story Template")

    if not st.session_state[SessionStateKeys.EDITED_TEMPLATE]:
        st.warning("Please select a template first.")
        if st.button("← Back to Story Parameters"):
            st.rerun()
        return

    edited_template = TemplateEditor.render(
        st.session_state[SessionStateKeys.EDITED_TEMPLATE]
    )
    st.session_state[SessionStateKeys.EDITED_TEMPLATE] = edited_template

    st.divider()
    if st.button(
        "Continue to Generate Story",
        use_container_width=True,
    ):
        advance_to_generate_story()
        st.rerun()


def render_generate_story_step() -> None:
    """Step 3: Generate and edit the story."""
    st.header("Step 3: Generate Story")

    if not st.session_state[SessionStateKeys.EDITED_TEMPLATE]:
        st.warning("Please complete the previous steps first.")
        if st.button("← Back to Story Parameters"):
            st.rerun()
        return

    if not st.session_state[SessionStateKeys.GENERATED_PAGES]:
        st.info("Click 'Generate Story' to create your storybook.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Template", use_container_width=True):
                back_to_edit_template()
                st.rerun()

        with col2:
            if st.button(
                "Generate Story",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Generating your story..."):
                    try:
                        processor = StoryProcessor()
                        character_name = st.session_state.get(
                            SessionStateKeys.CHAR_NAME, "Hero"
                        )
                        character_age = st.session_state.get(
                            SessionStateKeys.CHAR_AGE, 5
                        )
                        character_gender = st.session_state.get(
                            SessionStateKeys.CHAR_GENDER, Gender.boy
                        )
                        language = st.session_state.get(
                            SessionStateKeys.LANGUAGE, Language.english
                        )

                        generated_pages = processor.generate_story(
                            story_template=st.session_state[
                                SessionStateKeys.EDITED_TEMPLATE
                            ],
                            seed_images=st.session_state[SessionStateKeys.SEED_IMAGES],
                            metadata=st.session_state[SessionStateKeys.METADATA],
                            system_prompt=st.session_state[
                                SessionStateKeys.SYSTEM_PROMPT
                            ],
                            character_name=character_name,
                            character_age=character_age,
                            character_gender=character_gender,
                            language=language,
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
    else:
        updated_pages = StoryEditor.render(
            st.session_state[SessionStateKeys.GENERATED_PAGES]
        )
        st.session_state[SessionStateKeys.GENERATED_PAGES] = updated_pages

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← Back to Template", use_container_width=True):
                back_to_edit_template()
                st.rerun()

        with col2:
            if st.button("Regenerate Story", use_container_width=True):
                st.session_state[SessionStateKeys.GENERATED_PAGES] = []
                st.rerun()

        with col3:
            story_title = (
                st.session_state[SessionStateKeys.EDITED_TEMPLATE].default_title
                if st.session_state.get(SessionStateKeys.EDITED_TEMPLATE)
                else "Story"
            )

            zip_path = DownloadManager.create_archive(
                pages=st.session_state[SessionStateKeys.GENERATED_PAGES],
                story_title=story_title,
                character_name=st.session_state.get(SessionStateKeys.CHAR_NAME),
                character_age=st.session_state.get(SessionStateKeys.CHAR_AGE),
                character_gender=st.session_state.get(SessionStateKeys.CHAR_GENDER),
                language=st.session_state.get(SessionStateKeys.LANGUAGE),
                metadata=st.session_state.get(SessionStateKeys.METADATA),
                template=st.session_state.get(SessionStateKeys.EDITED_TEMPLATE),
                system_prompt=st.session_state.get(SessionStateKeys.SYSTEM_PROMPT),
            )

            if zip_path:
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download Story",
                        data=f.read(),
                        file_name=f"{DownloadManager.sanitize_filename(story_title)}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )


def main() -> None:
    initialize_session_state()

    current_step = st.session_state[SessionStateKeys.STEP]
    steps = [Step.story_parameters, Step.edit_template, Step.generate_story]

    current_index = steps.index(current_step)
    progress = (current_index + 1) // len(steps)
    st.caption(f"Step {current_index + 1} of {len(steps)}")
    st.progress(progress)

    if current_step == Step.story_parameters:
        render_story_parameters_step()
    elif current_step == Step.edit_template:
        render_edit_template_step()
    elif current_step == Step.generate_story:
        render_generate_story_step()


if __name__ == "__main__":
    main()
