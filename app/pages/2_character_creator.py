"""
StoryTime Character Creator Page
Create character reference images with different poses and art styles
"""

import streamlit as st
import os
from PIL import Image
from google import genai
from app.ai.character_generator import CharacterGenerator
from app.utils.settings import settings


def main():
    """Character Creator page with pose generation and style options"""

    try:
        settings.google_api_key
    except Exception:
        st.error("Warning: Please set your GOOGLE_API_KEY in your .env file")
        st.info("You can get an API key from: https://makersuite.google.com/app/apikey")
        st.stop()

    st.header("Character Creator")
    st.write(
        "Generate character reference images with front-facing and side profile poses"
    )

    st.divider()

    st.subheader("Character Settings")
    (col1,) = st.columns(1)

    with col1:
        character_images = st.file_uploader(
            "Upload Child's Photos (up to 3)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload 1-3 clear photos of the child for character reference",
        )

        character_name = st.text_input(
            "Character Name (Optional)",
            value="",
            help="Optional: Name for the character",
        )

        character_age = st.number_input(
            "Age",
            min_value=1,
            max_value=12,
            value=5,
            help="Age of the character (affects proportions)",
        )

        art_style = st.selectbox(
            "Art Style",
            ["Cartoon", "Watercolor", "Studio Ghibli", "Digital Art", "Pixar"],
            index=0,
            help="Choose the artistic style for the character reference",
        )

        gender = st.selectbox(
            "Gender",
            ["Boy", "Girl"],
            index=0,
            help="Character gender for appropriate styling and features",
        )

    st.divider()

    # Add validation for image count
    if character_images and len(character_images) > 3:
        st.error("Please upload a maximum of 3 photos.")
        st.stop()

    if character_images:
        st.write(f"**{len(character_images)} photo(s) uploaded**")

        if st.button(
            "Generate Character Reference",
            type="primary",
            width="stretch",
        ):
            with st.spinner("Generating character reference with both poses..."):
                try:
                    client = genai.Client(api_key=settings.google_api_key)
                    generator = CharacterGenerator(client=client, model=settings.model)

                    result_path = generator.generate_character_poses(
                        character_images=character_images,
                        character_name=character_name,
                        character_age=character_age,
                        gender=gender.lower(),
                        art_style=art_style.lower()
                        .replace(" ", "_")
                        .replace("studio_", ""),
                    )

                    if result_path:
                        st.success("Character reference generated successfully!")

                        st.write("**Generated Character Reference:**")
                        generated_image = Image.open(result_path)
                        st.image(generated_image, width="stretch")

                        with open(result_path, "rb") as file:
                            image_data = file.read()

                        filename = f"character_reference_{character_name or 'character'}_{art_style.lower().replace(' ', '_')}.png"

                        st.download_button(
                            "Download Character Reference",
                            data=image_data,
                            file_name=filename,
                            mime="image/png",
                            width="stretch",
                        )

                        try:
                            os.unlink(result_path)
                        except Exception:
                            pass
                    else:
                        st.error(
                            "Failed to generate character reference. Please try again."
                        )

                except Exception as e:
                    st.error(f"Error generating character reference: {str(e)}")
    else:
        st.info("Please upload 1-3 character photos to begin")


main()
