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

    def generate_character_reference(
        self,
        character_images,
        character_name: str,
        character_age: int,
        character_gender: str,
        character_info: str,
        art_style: str
    ) -> Optional[str]:
        """Generate character reference sheet from uploaded photos.

        Args:
            character_images: Uploaded character photos
            character_name: Name of the character
            character_age: Age of the character
            character_gender: Gender (boy/girl)
            character_info: Description of the character
            art_style: Art style to apply

        Returns:
            Path to generated character reference image, or None on failure
        """
        try:
            # Prepare images
            from PIL import Image as PILImage
            image_inputs = []
            for img in character_images:
                image_inputs.append(PILImage.open(img))

            # Include age in character info if not already present
            if str(character_age) not in character_info:
                character_info = f"{character_age} year old {character_info}"

            # Build prompt using the character generation template
            template = self.env.get_template("character_generation.j2")
            prompt = template.render(
                gender=character_gender,
                character_info=character_info,
                art_style=art_style,
                reference_note=f"Based on the {len(image_inputs)} uploaded photos of a {character_age} year old {character_gender}"
            )

            # Add character age emphasis and size requirements to prompt
            prompt += f"\n\nIMPORTANT: The character is {character_age} years old. Ensure the character's appearance, proportions, and features clearly reflect a {character_age}-year-old {character_gender}.\n"
            prompt += "\n\nIMAGE SIZE REQUIREMENTS:\n"
            prompt += "- Generate image in SQUARE format (1:1 aspect ratio)\n"
            prompt += "- Target dimensions: 800x800 pixels\n"
            prompt += "- Maintain consistent square size across all generated images\n"

            # Prepare contents for generation
            contents = [prompt] + image_inputs

            # Generate character reference with specific generation config
            from google.genai import types
            generation_config = types.GenerateContentConfig(
                temperature=0.4,
                top_p=1,
                top_k=32,
                max_output_tokens=8192,
                response_modalities=["Text", "Image"]
            )

            response = self._generate_content(contents, config=generation_config)

            if not response or not response.candidates:
                logger.warning("No response from AI for character reference generation")
                return None

            # Extract generated image
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    generated_image = PILImage.open(io.BytesIO(image_data))

                    # Resize to consistent square dimensions
                    target_size = 800

                    # Resize image to consistent size while maintaining aspect ratio
                    generated_image.thumbnail((target_size, target_size), PILImage.Resampling.LANCZOS)

                    # Create new square image with exact dimensions and paste resized image
                    final_image = PILImage.new('RGB', (target_size, target_size), (255, 255, 255))

                    # Center the resized image
                    x = (target_size - generated_image.width) // 2
                    y = (target_size - generated_image.height) // 2
                    final_image.paste(generated_image, (x, y))

                    # Save to temporary file
                    if temp_path := save_image_to_temp(
                        image=final_image,
                        suffix=Suffix.png,
                    ):
                        logger.info(f"Successfully generated character reference for {character_name} (size: {target_size}x{target_size})")
                        return temp_path

            logger.warning("No image found in AI response")
            return None

        except Exception as e:
            logger.error(f"Failed to generate character reference: {str(e)}")
            return None

    def generate(
        self,
        illustration_prompt: str,
        page_title: str,
        story_text: str = "",
        seed_images: Optional[List] = None,
        metadata: Optional[StoryMetadata] = None,
        system_prompt: Optional[str] = None,
        previous_pages: Optional[List[dict]] = None,
        previous_images: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Generate illustration for a story page using image_generation.j2 template.

        Args:
            illustration_prompt: Prompt describing the illustration
            page_title: Title of the current page
            story_text: Text content of the page
            seed_images: Optional seed images for visual reference (character reference)
            metadata: Optional metadata with art style and instructions
            system_prompt: Optional system prompt for generation
            previous_pages: Previous pages for context
            previous_images: Previous generated images for visual consistency

        Returns:
            Path to generated image file, or None on failure
        """
        try:
            # Prepare character reference images (seed images)
            character_images = []
            if seed_images:
                for img in seed_images:
                    try:
                        if isinstance(img, str):
                            character_images.append(Image.open(img))
                        else:
                            character_images.append(Image.open(img))
                    except Exception as e:
                        logger.warning(f"Failed to open seed image: {e}")

            # Prepare previous images for context (up to 5)
            context_images = []
            if previous_images:
                # Take up to 5 most recent images for context
                recent_images = previous_images[-5:] if len(previous_images) > 5 else previous_images
                for img_path in recent_images:
                    try:
                        context_images.append(Image.open(img_path))
                    except Exception as e:
                        logger.warning(f"Failed to open previous image: {e}")

            # Extract character info from session state or defaults
            # We can access this from streamlit session state if needed
            character_name = "Hero"
            character_age = 5
            character_gender = "child"

            # Try to extract from system prompt if available
            if metadata and metadata.instructions:
                # Simple extraction from instructions
                instructions_lower = metadata.instructions.lower()
                if "boy" in instructions_lower:
                    character_gender = "boy"
                elif "girl" in instructions_lower:
                    character_gender = "girl"

                # Try to extract age if mentioned
                import re
                age_match = re.search(r'(\d+)[\s-]?year', instructions_lower)
                if age_match:
                    character_age = int(age_match.group(1))

            # Use the image_generation.j2 template
            template = self.env.get_template("image_generation.j2")
            prompt = template.render(
                page_title=page_title,
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
                num_character_images=len(character_images),
                illustration_prompt=illustration_prompt,
                story_text=story_text,
                previous_pages=previous_pages,
                num_previous_images=len(context_images)
            )

            # Add any additional system instructions
            if system_prompt:
                prompt = f"{system_prompt}\n\n{prompt}"

            # Prepare contents: prompt + character reference + previous images for context
            contents = [prompt] + character_images + context_images

            # Generate image with specific generation config for consistency
            from google.genai import types
            generation_config = types.GenerateContentConfig(
                temperature=0.4,
                top_p=1,
                top_k=32,
                max_output_tokens=8192,
                response_modalities=["Text", "Image"]
            )

            response = self._generate_content(contents, config=generation_config)

            if not response or not response.candidates:
                logger.warning("No response from AI for image generation")
                return None

            # Extract generated image
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    generated_image = Image.open(io.BytesIO(image_data))

                    # Resize to consistent square dimensions
                    target_size = 800

                    # Resize image to consistent size while maintaining aspect ratio
                    generated_image.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

                    # Create new square image with exact dimensions and paste resized image
                    final_image = Image.new('RGB', (target_size, target_size), (255, 255, 255))

                    # Center the resized image
                    x = (target_size - generated_image.width) // 2
                    y = (target_size - generated_image.height) // 2
                    final_image.paste(generated_image, (x, y))

                    # Save to temporary file
                    if temp_path := save_image_to_temp(
                        image=final_image,
                        suffix=Suffix.png,
                    ):
                        logger.info(f"Successfully generated image for page: {page_title} (size: {target_size}x{target_size})")
                        return temp_path

            logger.warning("No image found in AI response")
            return None

        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            return None