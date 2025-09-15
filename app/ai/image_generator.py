import io
from typing import Optional
from PIL import Image
from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator
from app.utils.schemas import ArtStyle, Gender, StoryMetadata, Suffix
from app.utils.temp_file import save_image_to_temp
from google.genai import types


class ImageGenerator(BaseAIGenerator):
    ART_STYLE_DESCRIPTIONS = {
        ArtStyle.watercolor: "soft watercolor painting style, gentle brush strokes, flowing colors, artistic paper texture",
        ArtStyle.cartoon: "bright cartoon style, clean lines, vibrant colors, friendly and approachable",
        ArtStyle.ghibli: "Studio Ghibli anime style, soft cel animation, beautiful detailed eyes, magical atmosphere",
        ArtStyle.vintage: "vintage illustration style, classic storybook aesthetic, muted colors, nostalgic feel",
        ArtStyle.digital: "clean digital art style, smooth shading, modern illustration, crisp details",
        ArtStyle.pixar: "Pixar 3D animation style, expressive features, warm lighting, high-quality rendering",
    }

    def __init__(self, client: genai.Client, model: str):
        super().__init__(client, model)

    def generate_character_reference(
        self,
        character_images,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        system_prompt: str,
        art_style: ArtStyle,
    ) -> Optional[str]:
        try:
            image_inputs = [Image.open(fp=img) for img in character_images]
            art_style_description = self.ART_STYLE_DESCRIPTIONS[art_style]

            template = self.env.get_template("character_generation.j2")
            prompt = template.render(
                gender=character_gender,
                character_age=character_age,
                character_name=character_name,
                system_prompt=system_prompt,
                art_style_description=art_style_description,
            )

            contents = [prompt] + image_inputs

            generation_config = types.GenerateContentConfig(
                temperature=0.4,
                top_p=1,
                top_k=32,
                max_output_tokens=8192,
                response_modalities=["Text", "Image"],
            )

            response = self._generate_content(contents, config=generation_config)

            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    generated_image = Image.open(io.BytesIO(initial_bytes=image_data))
                    target_size = 800
                    generated_image.thumbnail(
                        (target_size, target_size),
                        Image.Resampling.LANCZOS,
                    )
                    final_image = Image.new(
                        "RGB",
                        (target_size, target_size),
                        (255, 255, 255),
                    )

                    x = (target_size - generated_image.width) // 2
                    y = (target_size - generated_image.height) // 2
                    final_image.paste(generated_image, (x, y))

                    if temp_path := save_image_to_temp(
                        image=final_image,
                        suffix=Suffix.png,
                    ):
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
        seed_images: Optional[list] = None,
        metadata: Optional[StoryMetadata] = None,
        system_prompt: Optional[str] = None,
        previous_pages: Optional[list[dict]] = None,
        previous_images: Optional[list[str]] = None,
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
                recent_images = (
                    previous_images[-5:]
                    if len(previous_images) > 5
                    else previous_images
                )
                for img_path in recent_images:
                    try:
                        context_images.append(Image.open(img_path))
                    except Exception as e:
                        logger.warning(f"Failed to open previous image: {e}")

            # Extract character info from metadata or use defaults
            character_name = "Hero"
            character_age = 5
            character_gender = "child"

            if metadata:
                # Use metadata properties directly
                character_name = getattr(metadata, "character_name", character_name)
                character_age = getattr(metadata, "age", character_age)

                # Handle gender enum
                if hasattr(metadata, "gender"):
                    gender_value = metadata.gender
                    # If it's an enum, get its value
                    if hasattr(gender_value, "value"):
                        character_gender = gender_value.value
                    else:
                        character_gender = str(gender_value)

            # Get art style description if metadata contains art style
            art_style_description = None
            if metadata and hasattr(metadata, "art_style"):
                art_style_description = self.ART_STYLE_DESCRIPTIONS.get(
                    metadata.art_style
                )

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
                num_previous_images=len(context_images),
                system_prompt=system_prompt,
                art_style_description=art_style_description,
            )

            # Prepare contents: prompt + character reference + previous images for context
            contents = [prompt] + character_images + context_images

            # Generate image with specific generation config for consistency
            from google.genai import types

            generation_config = types.GenerateContentConfig(
                temperature=0.4,
                top_p=1,
                top_k=32,
                max_output_tokens=8192,
                response_modalities=["Text", "Image"],
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
                    generated_image.thumbnail(
                        (target_size, target_size), Image.Resampling.LANCZOS
                    )

                    # Create new square image with exact dimensions and paste resized image
                    final_image = Image.new(
                        "RGB", (target_size, target_size), (255, 255, 255)
                    )

                    # Center the resized image
                    x = (target_size - generated_image.width) // 2
                    y = (target_size - generated_image.height) // 2
                    final_image.paste(generated_image, (x, y))

                    # Save to temporary file
                    if temp_path := save_image_to_temp(
                        image=final_image,
                        suffix=Suffix.png,
                    ):
                        logger.info(
                            f"Successfully generated image for page: {page_title} (size: {target_size}x{target_size})"
                        )
                        return temp_path

            logger.warning("No image found in AI response")
            return None

        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            return None
