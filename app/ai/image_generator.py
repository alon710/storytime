"""Image generation component for StoryTime application."""

import io
from typing import Optional, List
from PIL import Image
from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator
from app.utils.schemas import StoryMetadata, Suffix
from app.utils.temp_file import save_image_to_temp


class ImageGenerator(BaseAIGenerator):
    """AI-powered image generator for story illustrations."""

    def __init__(self, client: genai.Client, model: str):
        super().__init__(client, model)

    def generate(
        self,
        illustration_prompt: str,
        page_title: str,
        story_text: str = "",
        seed_images: Optional[List] = None,
        metadata: Optional[StoryMetadata] = None,
        system_prompt: Optional[str] = None,
        previous_pages: Optional[List[dict]] = None,
    ) -> Optional[str]:
        """Generate illustration for a story page.

        Args:
            illustration_prompt: Prompt describing the illustration
            page_title: Title of the current page
            story_text: Text content of the page
            seed_images: Optional seed images for visual reference
            metadata: Optional metadata with art style and instructions
            system_prompt: Optional system prompt for generation
            previous_pages: Previous pages for context

        Returns:
            Path to generated image file, or None on failure
        """
        # Prepare image inputs
        image_inputs = []
        if seed_images:
            for img in seed_images[:3]:  # Limit to 3 seed images
                try:
                    image_inputs.append(Image.open(img))
                except Exception as e:
                    logger.warning(f"Failed to open seed image: {e}")

        # Build generation prompt
        prompt_parts = []

        # System instructions
        prompt_parts.append("Generate a children's book illustration based on the following:")

        if system_prompt:
            prompt_parts.append(f"\nSystem Instructions: {system_prompt}")

        if metadata:
            if metadata.art_style:
                prompt_parts.append(f"\nArt Style: {metadata.art_style.value}")
            if metadata.instructions:
                prompt_parts.append(f"\nSpecial Instructions: {metadata.instructions}")

        # Page context
        prompt_parts.append(f"\nPage Title: {page_title}")
        prompt_parts.append(f"Story Text: {story_text}")
        prompt_parts.append(f"\nIllustration Description: {illustration_prompt}")

        # Previous pages context for consistency
        if previous_pages and len(previous_pages) > 0:
            prompt_parts.append("\nPrevious story context for continuity:")
            for prev in previous_pages[-2:]:  # Last 2 pages for context
                prompt_parts.append(f"- {prev.get('title', '')}: {prev.get('text', '')[:100]}...")

        if seed_images:
            prompt_parts.append(f"\nUsing {len(image_inputs)} seed image(s) as visual reference.")

        prompt_parts.append("\nCreate a vibrant, child-friendly illustration that captures the scene described.")

        full_prompt = "\n".join(prompt_parts)

        # Prepare contents for generation
        contents = [full_prompt] + image_inputs

        # Generate image
        try:
            response = self._generate_content(contents, ["Text", "Image"])

            if not response or not response.candidates:
                logger.warning("No response from AI for image generation")
                return None

            # Extract generated image
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    generated_image = Image.open(io.BytesIO(image_data))

                    # Save to temporary file
                    if temp_path := save_image_to_temp(
                        image=generated_image,
                        suffix=Suffix.png,
                    ):
                        logger.info(f"Successfully generated image for page: {page_title}")
                        return temp_path

            logger.warning("No image found in AI response")
            return None

        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            return None