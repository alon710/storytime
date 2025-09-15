import streamlit as st

from app.ui.components.metadata_manager import MetadataManager
from app.ui.components.seed_image_uploader import SeedImageUploader
from app.ui.components.template_editor import TemplateEditor
from app.ui.components.story_editor import StoryEditor
from app.ai.story_processor import StoryProcessor
from app.utils.schemas import SessionStateKeys
from app.utils.download_manager import DownloadManager
from app.utils.utils import initialize_session_state, load_story_templates


def render_metadata_step() -> None:
    st.header("Step 1: Story Configuration")
    st.write("Configure the main parameters for your story.")
    MetadataManager.render()


def render_seed_images_step() -> None:
    st.header("Step 2: Character Reference")
    st.write("Provide a visual reference for your story's main character.")

    metadata = st.session_state.get(SessionStateKeys.METADATA)
    seed_data = SeedImageUploader.render(metadata=metadata)

    if seed_data:
        st.session_state[SessionStateKeys.SEED_IMAGES] = seed_data.images


def render_story_template_step() -> None:
    st.header("Step 3: Load and Edit Story Template")

    templates = load_story_templates()

    if not templates:
        st.error("No story templates found in app/story_templates/")
        return

    selected_template_name = st.selectbox(
        "Select a story template",
        options=list(templates.keys()),
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
    st.header("Step 4: Generate Story")

    metadata = st.session_state.get(SessionStateKeys.METADATA)
    if not metadata:
        st.warning("Please complete Step 1: Story Configuration first.")
        return

    if st.button("Generate Story", use_container_width=True):
        with st.spinner("Generating your story..."):
            try:
                processor = StoryProcessor()

                generated_pages = processor.generate_story(
                    story_template=st.session_state[SessionStateKeys.EDITED_TEMPLATE],
                    seed_images=st.session_state.get(SessionStateKeys.SEED_IMAGES, []),
                    metadata=metadata,
                )

                if generated_pages:
                    st.session_state[SessionStateKeys.GENERATED_PAGES] = generated_pages
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

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Regenerate Story", use_container_width=True):
                st.session_state[SessionStateKeys.GENERATED_PAGES] = []
                st.rerun()

        with col2:
            story_title = (
                st.session_state[SessionStateKeys.EDITED_TEMPLATE].default_title
                if st.session_state.get(SessionStateKeys.EDITED_TEMPLATE)
                else "Story"
            )

            metadata = st.session_state.get(SessionStateKeys.METADATA)
            if metadata:
                zip_path = DownloadManager.create_archive(
                    pages=st.session_state[SessionStateKeys.GENERATED_PAGES],
                    story_title=story_title,
                    metadata=metadata,
                    template=st.session_state.get(SessionStateKeys.EDITED_TEMPLATE),
                )
            else:
                zip_path = None

            if zip_path:
                with open(zip_path, "rb") as f:
                    if st.download_button(
                        label="Download Story Archive",
                        data=f.read(),
                        file_name=f"{story_title}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    ):
                        st.success("Download started!")
            else:
                st.error("Could not create download archive")


def main() -> None:
    initialize_session_state()

    render_metadata_step()
    st.divider()

    render_seed_images_step()
    st.divider()

    render_story_template_step()
    st.divider()

    render_generation_step()


if __name__ == "__main__":
    main()
