"""Character generation module for StoryTime."""

import io
import tempfile
from typing import Optional
from PIL import Image
from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator
from app.utils.schemas import ArtStyle, Gender


class CharacterGenerator(BaseAIGenerator):
    def __init__(self, client: genai.Client, model: str):
        super().__init__(client, model)

    def generate(self, *args, **kwargs):
        return self.generate_character_poses(*args, **kwargs)

    def generate_character_poses(
        self,
        character_images,
        character_name: str = "",
        character_age: int = 5,
        art_style: ArtStyle = ArtStyle.cartoon,
        gender: Gender = Gender.boy,
    ) -> Optional[str]:
        return self._with_error_handling(
            "character pose generation",
            self._generate_character_poses_impl,
            character_images,
            character_name,
            character_age,
            art_style,
            gender,
        )

    def _generate_character_poses_impl(
        self,
        character_images,
        character_name: str,
        character_age: int,
        art_style: str,
        gender: str,
    ) -> Optional[str]:
        character_image_pils = self._prepare_character_images(character_images)
        style_prompt = self._get_style_prompt(art_style)
        character_info = self._build_character_info(character_name, character_age, gender)
        system_prompt = self._build_system_prompt(gender, character_info, style_prompt, len(character_image_pils), art_style)
        
        self._log_generation_start(art_style, character_name, character_age, gender, len(character_image_pils))
        
        contents = [system_prompt] + character_image_pils
        response = self._generate_content(contents, ["Text", "Image"])
        
        if response is None:
            return None
            
        return self._process_generation_response(response, art_style, character_name, gender)

    def _prepare_character_images(self, character_images):
        character_image_pils = []
        for char_img in character_images:
            char_img.seek(0)
            character_image_pils.append(Image.open(char_img))
            char_img.seek(0)
        return character_image_pils

    def _get_style_prompt(self, art_style: str) -> str:
        style_modifiers = {
            ArtStyle.watercolor: "soft watercolor painting style, gentle brush strokes, flowing colors, artistic paper texture",
            ArtStyle.cartoon: "bright cartoon style, clean lines, vibrant colors, friendly and approachable",
            ArtStyle.ghibli: "Studio Ghibli anime style, soft cel animation, beautiful detailed eyes, magical atmosphere",
            ArtStyle.digital: "clean digital art style, smooth shading, modern illustration, crisp details",
            ArtStyle.pixar: "Pixar 3D animation style, expressive features, warm lighting, high-quality rendering",
        }
        
        return style_modifiers.get(art_style.lower(), style_modifiers["cartoon"])

    def _build_character_info(self, character_name: str, character_age: int, gender: str) -> str:
        character_info = ""
        if character_name:
            character_info += f"Character name: {character_name}, "
        character_info += f"{character_age}-year-old {gender}"
        return character_info

    def _build_system_prompt(self, gender: str, character_info: str, style_prompt: str, num_images: int, art_style: str) -> str:
        reference_note = f"I have provided {num_images} reference photo(s)"
        
        return f"""
        Create a character reference sheet showing the same {gender} in TWO different poses within a SINGLE image:

        LEFT SIDE: Front-facing view (looking directly at camera/viewer)
        RIGHT SIDE: Side profile view (facing to the right)

        Character details: {character_info}
        Art style: {style_prompt}

        REQUIREMENTS:
        - {reference_note} of the {gender} - use all photos to capture the {gender}'s appearance, features, and characteristics
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

    def _log_generation_start(self, art_style: str, character_name: str, character_age: int, gender: str, num_images: int):
        logger.debug(
            "Generating character reference poses",
            extra={
                "art_style": art_style,
                "character_name": character_name,
                "character_age": character_age,
                "gender": gender,
                "num_reference_images": num_images,
            },
        )

    def _process_generation_response(self, response, art_style: str, character_name: str, gender: str) -> Optional[str]:
        generated_image = None
        response_text = ""

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                response_text += part.text
            elif part.inline_data is not None:
                image_data = part.inline_data.data
                generated_image = Image.open(io.BytesIO(image_data))

                temp_path = self._save_generated_image(generated_image)
                
                self._log_generation_success(art_style, temp_path, character_name, gender)
                self._log_response_text(response_text)
                return temp_path

        logger.warning(
            "No character image generated - text response only",
            extra={"response_text": response_text[:200]},
        )
        return None

    def _save_generated_image(self, generated_image: Image.Image) -> str:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            generated_image.save(tmp_file.name, "PNG")
            return tmp_file.name

    def _log_generation_success(self, art_style: str, temp_path: str, character_name: str, gender: str):
        logger.info(
            "Successfully generated character reference poses",
            extra={
                "art_style": art_style,
                "temp_path": temp_path,
                "character_name": character_name,
                "gender": gender,
            },
        )

    def _log_response_text(self, response_text: str):
        logger.debug(
            "Gemini character generation response",
            extra={"response_text": response_text[:200]},
        )
