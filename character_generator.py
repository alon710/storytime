"""Character generation module for StoryTime."""

import io
import tempfile
from typing import Optional
from PIL import Image
from google import genai
from google.genai import types
from logger import logger


class CharacterGenerator:
    """Handles AI-powered character reference generation using Google GenAI."""

    def __init__(self, client: genai.Client, model: str):
        """Initialize generator with GenAI client and model."""
        self.client = client
        self.model = model

    def generate_character_poses(
        self,
        character_images,
        character_name: str = "",
        character_age: int = 5,
        art_style: str = "cartoon",
    ) -> Optional[str]:
        """Generate character reference with front and side poses in a single image using multiple reference photos."""
        try:
            # Process all uploaded character images
            character_image_pils = []
            for char_img in character_images:
                char_img.seek(0)
                character_image_pils.append(Image.open(char_img))
                char_img.seek(0)

            # Style-specific modifiers
            style_modifiers = {
                "watercolor": "soft watercolor painting style, gentle brush strokes, flowing colors, artistic paper texture",
                "cartoon": "bright cartoon style, clean lines, vibrant colors, friendly and approachable",
                "ghibli": "Studio Ghibli anime style, soft cel animation, beautiful detailed eyes, magical atmosphere",
                "digital": "clean digital art style, smooth shading, modern illustration, crisp details",
                "pixar": "Pixar 3D animation style, expressive features, warm lighting, high-quality rendering"
            }

            style_prompt = style_modifiers.get(art_style.lower(), style_modifiers["cartoon"])
            
            character_info = ""
            if character_name:
                character_info = f"Character name: {character_name}, "
            character_info += f"{character_age}-year-old child"

            reference_note = f"I have provided {len(character_image_pils)} reference photo(s)" if len(character_image_pils) > 1 else "I have provided a reference photo"
            
            system_prompt = f"""
            Create a character reference sheet showing the same child in TWO different poses within a SINGLE image:

            LEFT SIDE: Front-facing view (looking directly at camera/viewer)
            RIGHT SIDE: Side profile view (facing to the right)

            Character details: {character_info}
            Art style: {style_prompt}

            REQUIREMENTS:
            - {reference_note} of the child - use all photos to capture the child's appearance, features, and characteristics
            - Synthesize features from all reference images to create a consistent character design
            - Both poses should be consistent - same clothing, hair, and features
            - Clear split composition with both poses in the same image
            - No text or labels in the image
            - Child-friendly, warm, and welcoming style
            - Both poses should be full body or at least torso up
            - Maintain consistent proportions between both poses
            - Apply the {art_style} style uniformly to both poses
            - Clean white or simple background
            
            COMPOSITION:
            - Single cohesive image with two character poses
            - Left pose: Front view facing forward
            - Right pose: Side profile view
            - Both poses should be clearly visible and well-proportioned
            - Consistent lighting and art style across both poses
            """

            logger.debug(
                "Generating character reference poses",
                extra={
                    "art_style": art_style,
                    "character_name": character_name,
                    "character_age": character_age,
                    "num_reference_images": len(character_image_pils)
                }
            )

            # Create contents with system prompt and all character images
            contents = [system_prompt] + character_image_pils

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["Text", "Image"]
                ),
            )

            if not response or not response.candidates:
                logger.warning("No response received from Gemini API for character generation")
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
                        "Successfully generated character reference poses",
                        extra={
                            "art_style": art_style,
                            "temp_path": temp_path,
                            "character_name": character_name
                        },
                    )
                    logger.debug(
                        "Gemini character generation response",
                        extra={"response_text": response_text[:200]},
                    )
                    return temp_path

            logger.warning(
                "No character image generated - text response only",
                extra={"response_text": response_text[:200]},
            )
            return None

        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "art_style": art_style,
                "character_name": character_name
            }
            
            if hasattr(e, 'status_code'):
                error_details["status_code"] = e.status_code
            if hasattr(e, 'response'):
                error_details["response"] = str(e.response)
            
            logger.error("Character generation failed", extra=error_details, exc_info=True)
            return None