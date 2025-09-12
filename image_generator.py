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
        previous_pages: list[dict] | None = None,
        previous_images: list[str] | None = None,
    ) -> Optional[str]:
        """Generate illustration using character reference and custom prompt."""
        try:
            character_image.seek(0)
            character_image_pil = Image.open(character_image)
            character_image.seek(0)

            context_info = (
                f"\nStory context: {story_text}" if story_text.strip() else ""
            )
            
            # Build previous pages context for visual consistency
            previous_context = ""
            if previous_pages:
                previous_context = "\n\nPrevious illustrations for visual continuity:\n"
                for i, page in enumerate(previous_pages[-3:], 1):  # Last 3 pages only
                    previous_context += f"Page {i} ({page.get('title', '')}): {page.get('illustration_prompt', '')}\n"
                    
            # Load previous images for visual continuity
            previous_image_pils = []
            if previous_images:
                # Limit to last 2-3 images to manage API request size
                recent_images = previous_images[-3:] if len(previous_images) > 3 else previous_images
                logger.info(
                    "Including previous images for visual continuity", 
                    extra={
                        "page_title": page_title, 
                        "previous_image_count": len(recent_images),
                        "total_previous_images": len(previous_images)
                    }
                )
                
                for img_path in recent_images:
                    try:
                        previous_img = Image.open(img_path)
                        previous_image_pils.append(previous_img)
                        logger.debug("Successfully loaded previous image", extra={"image_path": img_path})
                    except Exception as e:
                        logger.warning(
                            "Failed to load previous image", 
                            extra={
                                "image_path": img_path, 
                                "error": str(e)
                            }
                        )

            # Add context about previous images if they're included
            image_context_note = ""
            if previous_image_pils:
                image_context_note = f"\n\nVisual reference: You are provided with {len(previous_image_pils)} previous illustration(s) from this storybook for visual consistency. Use these to maintain consistent character appearance, art style, and overall visual continuity."

            system_prompt = f"""
            Generate a storybook style children's book illustration without text.
            
            Book: "{book_title}" | Page: "{page_title}"
            Character: {character_name} ({character_age}-year-old {character_gender.lower()})
            Request: {illustration_prompt}{context_info}{previous_context}{image_context_note}
            
            Requirements:
            - Use character image reference for visual consistency
            - Maintain storybook style throughout book
            - Keep consistent character appearance and proportions
            - Create warm, child-friendly scene for ages 2-8
            - Single cohesive image without text or multiple panels
            - Maintain visual consistency with previous illustrations
            
            COMPOSITION REQUIREMENTS:
            - Fill the ENTIRE image space with the scene - no borders, frames, or vignettes
            - Extend the scene to all edges of the canvas
            - No abstract backgrounds or wallpaper patterns - use full environmental scenes
            - Characters and objects should occupy meaningful space in the composition
            - Background should be a complete environment (room, outdoor scene, etc.) not abstract patterns
            """

            # Include character image, prompt, and any previous images in the API call
            contents = [system_prompt, illustration_prompt, character_image_pil] + previous_image_pils
            
            logger.debug(
                "Sending generation request to Gemini",
                extra={
                    "page_title": page_title,
                    "total_content_items": len(contents),
                    "has_previous_images": len(previous_image_pils) > 0,
                    "previous_pages_count": len(previous_pages) if previous_pages else 0
                }
            )
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
