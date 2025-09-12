"""
StoryTime Story Generator Page
Create custom illustrated PDF storybooks with dynamic page creation
"""

import streamlit as st
import os
from pathlib import Path
from story_processor import StoryProcessor
from config import settings


def main():
    """Story Generator page with dynamic page creation interface"""
    
    try:
        settings.google_api_key
    except Exception:
        st.error("Warning: Please set your GOOGLE_API_KEY in your .env file")
        st.info("You can get an API key from: https://makersuite.google.com/app/apikey")
        st.stop()

    if "pages" not in st.session_state:
        st.session_state.pages = [
            {
                "title": "Adventure Morning",
                "story_text": "Our hero wakes up with Barvaz, their duck-shaped doll. 'Today we fly!' says Mom. The hero feels curious and excited.",
                "illustration_prompt": "Hero in cozy pajamas holding Barvaz (a cute duck-shaped doll), standing in a bright bedroom with morning sunlight streaming through the window",
            },
            {
                "title": "Packing Together",
                "story_text": "Hero helps put clothes and Barvaz in the suitcase. 'Quack, I'm ready too!' Barvaz seems to say.",
                "illustration_prompt": "Hero carefully placing Barvaz (duck-shaped doll) into a colorful suitcase, surrounded by folded clothes, simple bedroom background",
            },
            {
                "title": "The Airport Ride",
                "story_text": "In the car to the airport, hero looks out the window. 'Airplanes, here we come!' says Dad.",
                "illustration_prompt": "Hero sitting in a car seat, holding Barvaz (duck doll) on their lap, looking excitedly through the car window at the passing scenery",
            },
        ]

    st.header("Book Settings")
    col1, col2 = st.columns(2)

    with col1:
        book_title = st.text_input("Book Title", value="My Adventure")
        character_name = st.text_input("Character Name", value="Alex")

    with col2:
        character_gender = st.selectbox("Gender", ["Girl", "Boy"])
        character_age = st.number_input("Age", min_value=1, max_value=12, value=5)

    character_image = st.file_uploader(
        "Upload Character Photo", type=["jpg", "jpeg", "png"]
    )
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
        if not character_image:
            missing_fields.append("Character Photo")
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
                    character_image=character_image,
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
                        with open(results["pdf_path"], "rb") as file:
                            pdf_data = file.read()

                        # Display PDF viewer
                        st.subheader("Preview Your Storybook")
                        st.write("PDF Viewer:")
                        
                        # Use Streamlit's built-in PDF viewer
                        with open(results["pdf_path"], "rb") as pdf_file:
                            st.download_button(
                                "Download PDF", 
                                data=pdf_file.read(),
                                file_name=f"{book_title.replace(' ', '_')}_storybook.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        
                        st.download_button(
                            "Download Illustrated Storybook",
                            data=pdf_data,
                            file_name=f"{book_title.replace(' ', '_')}_storybook.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

                        st.info(
                            f"Generated {results['pages_processed']} illustrations in {results['processing_time']:.1f} seconds"
                        )
                else:
                    st.error(f"Failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
else:
    main()