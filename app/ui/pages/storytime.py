import streamlit as st

from app.ui.components.seed_image_uploader import SeedImageUploader
from app.ui.components.template_editor import TemplateEditor
from app.ui.components.story_editor import StoryEditor
from app.ai.story_processor import StoryProcessor
from app.utils.schemas import Gender, Language, SessionStateKeys
from app.utils.download_manager import DownloadManager
from app.utils.utils import initialize_session_state, load_story_templates


def render_seed_images_step() -> None:
    st.header("Step 1: Upload Seed Images")
    st.write("Upload images to use as visual references for your story.")
    seed_data = SeedImageUploader.render()

    if seed_data:
        st.session_state[SessionStateKeys.SEED_IMAGES] = seed_data.images
        st.session_state[SessionStateKeys.METADATA] = seed_data.metadata


def render_story_template_step() -> None:
    st.header("Step 2: Load and Edit Story Template")

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
    if st.button("Generate Story", width="stretch"):
        with st.spinner("Generating your story..."):
            try:
                processor = StoryProcessor()
                character_name = st.session_state.get(
                    SessionStateKeys.CHAR_NAME, "Hero"
                )
                character_age = st.session_state.get(SessionStateKeys.CHAR_AGE, 5)
                character_gender = st.session_state.get(
                    SessionStateKeys.CHAR_GENDER, Gender.boy
                )
                language = st.session_state.get(
                    SessionStateKeys.LANGUAGE, Language.english
                )

                if hasattr(character_gender, "value"):
                    character_gender = character_gender.value
                if hasattr(language, "value"):
                    language = language.value

                metadata = st.session_state.get(SessionStateKeys.METADATA)
                if metadata:
                    metadata.character_name = character_name
                    metadata.age = character_age
                    metadata.gender = character_gender
                    metadata.language = language

                system_prompt = st.session_state.get(SessionStateKeys.SYSTEM_PROMPT)
                if not system_prompt:
                    system_prompt = st.session_state.get(
                        SessionStateKeys.SYSTEM_PROMPT_SEED, ""
                    )

                generated_pages = processor.generate_story(
                    story_template=st.session_state[SessionStateKeys.EDITED_TEMPLATE],
                    seed_images=st.session_state[SessionStateKeys.SEED_IMAGES],
                    metadata=metadata,
                    system_prompt=system_prompt,
                    character_name=character_name,
                    character_age=character_age,
                    character_gender=character_gender,
                    language=language,
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
    render_seed_images_step()
    st.divider()
    render_story_template_step()
    st.divider()
    render_generation_step()


if __name__ == "__main__":
    main()
