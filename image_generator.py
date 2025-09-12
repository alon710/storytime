"""Image generation module for StoryTime."""

import io
import tempfile
from typing import Optional
from PIL import Image
from google import genai
from google.genai import types
from logger import logger


class ImageGenerator:
    """Handles AI-powered illustration generation using Google GenAI."""

    def __init__(self, client: genai.Client, model: str):
        """Initialize generator with GenAI client and model."""
        self.client = client
        self.model = model

    def generate(
        self,
        character_image,
        character_name: str,
        character_age: int,
        character_gender: str,
        illustration_prompt: str,
        book_title: str,
        page_title: str,
        story_text: str = "",
    ) -> Optional[str]:
        """Generate illustration using character reference and custom prompt."""
        try:
            character_image.seek(0)
            character_image_pil = Image.open(character_image)
            character_image.seek(0)

            context_info = (
                f"\nStory context: {story_text}" if story_text.strip() else ""
            )

            system_prompt = f"""
            Generate a storybook style children's book illustration without text.
            
            Book: "{book_title}" | Page: "{page_title}"
            Character: {character_name} ({character_age}-year-old {character_gender.lower()})
            Request: {illustration_prompt}{context_info}
            
            Requirements:
            - Use character image reference for visual consistency
            - Maintain storybook style throughout book
            - Keep consistent character appearance and proportions
            - Create warm, child-friendly scene for ages 2-8
            - Single cohesive image without text or multiple panels
            
            COMPOSITION REQUIREMENTS:
            - Fill the ENTIRE image space with the scene - no borders, frames, or vignettes
            - Extend the scene to all edges of the canvas
            - No abstract backgrounds or wallpaper patterns - use full environmental scenes
            - Characters and objects should occupy meaningful space in the composition
            - Background should be a complete environment (room, outdoor scene, etc.) not abstract patterns
            """

            contents = [system_prompt, illustration_prompt, character_image_pil]
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["Text", "Image"]
                ),
            )

            if not response or not response.candidates:
                logger.warning("No response received from Gemini API")
                return None

            generated_image = None
            response_text = ""

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    response_text += part.text
                elif part.inline_data is not None:
                    image_data = part.inline_data.data
                    generated_image = Image.open(io.BytesIO(image_data))

                    with tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    ) as tmp_file:
                        generated_image.save(tmp_file.name, "PNG")
                        temp_path = tmp_file.name

                    logger.info(
                        "Successfully generated image for page",
                        extra={"page_title": page_title, "temp_path": temp_path},
                    )
                    logger.debug(
                        "Gemini response text",
                        extra={"response_text": response_text[:200]},
                    )
                    return temp_path

            logger.warning(
                "No image generated for page - text response only",
                extra={"page_title": page_title, "response_text": response_text[:200]},
            )
            return None

        except Exception as e:
            error_details = {
                "page_title": page_title,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            
            if hasattr(e, 'status_code'):
                error_details["status_code"] = e.status_code
            if hasattr(e, 'response'):
                error_details["response"] = str(e.response)
            
            logger.error("Image generation failed", extra=error_details, exc_info=True)
            return None
