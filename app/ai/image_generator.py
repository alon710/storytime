"""Image generation module for StoryTime."""

import io
import tempfile
from typing import Optional
from PIL import Image
from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator


class ImageGenerator(BaseAIGenerator):
    """Handles AI-powered illustration generation using Google GenAI."""

    def __init__(self, client: genai.Client, model: str):
        """Initialize generator with GenAI client and model."""
        super().__init__(client, model)

    def generate(
        self,
        character_images,
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
        """Generate illustration using multiple character references and custom prompt."""
        return self._with_error_handling(
            "image generation",
            self._generate_impl,
            character_images,
            character_name,
            character_age,
            character_gender,
            illustration_prompt,
            book_title,
            page_title,
            story_text,
            previous_pages,
            previous_images,
        )

    def _generate_impl(
        self,
        character_images,
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
        # Process all uploaded character images
        character_image_pils = []
        for char_img in character_images:
            char_img.seek(0)
            character_image_pils.append(Image.open(char_img))
            char_img.seek(0)

        context_info = f"\nStory context: {story_text}" if story_text.strip() else ""

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
            recent_images = (
                previous_images[-3:] if len(previous_images) > 3 else previous_images
            )
            logger.info(
                "Including previous images for visual continuity",
                page_title=page_title,
                previous_image_count=len(recent_images),
                total_previous_images=len(previous_images),
            )

            for img_path in recent_images:
                try:
                    previous_img = Image.open(img_path)
                    previous_image_pils.append(previous_img)
                    logger.debug(
                        "Successfully loaded previous image",
                        image_path=img_path,
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to load previous image",
                        image_path=img_path,
                        error=str(e),
                    )

        character_context_note = f"Character reference: I have provided {len(character_image_pils)} reference photo(s) of {character_name}. Use all photos to capture the child's appearance, features, and characteristics accurately."

        image_context_note = ""
        if previous_image_pils:
            image_context_note = f"\n\nVisual reference: You are provided with {len(previous_image_pils)} previous illustration(s) from this storybook for visual consistency. Use these to maintain consistent character appearance, art style, and overall visual continuity."

        system_prompt = f"""
        Generate a storybook style children's book illustration without text.
        
        Book: "{book_title}" | Page: "{page_title}"
        Character: {character_name} ({character_age}-year-old {character_gender.lower()})
        {character_context_note}
        Request: {illustration_prompt}{context_info}{previous_context}{image_context_note}
        
        Requirements:
        - Use all character reference photos for visual consistency - synthesize features from all images
        - Maintain storybook style throughout book
        - Keep consistent character appearance and proportions based on all reference images
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

        # Include all character images, prompt, and any previous images in the API call
        contents = (
            [system_prompt, illustration_prompt]
            + character_image_pils
            + previous_image_pils
        )

        logger.debug(
            "Sending generation request to Gemini",
            system_prompt=system_prompt,
            illustration_prompt=illustration_prompt,
            page_title=page_title,
            total_content_items=len(contents),
            character_images_count=len(character_image_pils),
            has_previous_images=len(previous_image_pils) > 0,
            previous_pages_count=len(previous_pages) if previous_pages else 0,
        )
        response = self._generate_content(contents, ["Text", "Image"])
        if response is None:
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
                    page_title=page_title,
                    temp_path=temp_path,
                )
                logger.debug(
                    "Gemini response text",
                    response_text=response_text[:200],
                )
                return temp_path

        logger.warning(
            "No image generated for page - text response only",
            page_title=page_title,
            response_text=response_text[:200],
        )
        return None
