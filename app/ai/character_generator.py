import io
from typing import Optional
from PIL import Image
from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator
from app.utils.schemas import ArtStyle, Gender, Suffix
from app.utils.temp_file import save_image_to_temp


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
        gender: Gender,
    ) -> Optional[str]:
        character_image_pils = self._prepare_character_images(character_images)
        character_info = self._build_character_info(
            character_name, character_age, gender
        )
        system_prompt = self._build_system_prompt(
            gender, character_info, len(character_image_pils), art_style
        )

        self._log_generation_start(
            art_style, character_name, character_age, gender, len(character_image_pils)
        )

        contents = [system_prompt] + character_image_pils
        response = self._generate_content(contents, ["Text", "Image"])

        if response is None:
            return None

        return self._process_generation_response(
            response, art_style, character_name, gender
        )

    def _prepare_character_images(self, character_images):
        character_image_pils = []
        for char_img in character_images:
            char_img.seek(0)
            character_image_pils.append(Image.open(char_img))
            char_img.seek(0)
        return character_image_pils

    def _build_character_info(
        self,
        character_name: str,
        character_age: int,
        gender: Gender,
    ) -> str:
        character_info = ""
        if character_name:
            character_info += f"Character name: {character_name}, "
        character_info += f"{character_age}-year-old {gender}"
        return character_info

    def _build_system_prompt(
        self,
        gender: Gender,
        character_info: str,
        num_images: int,
        art_style: str,
    ) -> str:
        reference_note = f"I have provided {num_images} reference photo(s)"

        template = self.env.get_template("character_generation.j2")
        return template.render(
            gender=gender,
            character_info=character_info,
            reference_note=reference_note,
            art_style=art_style.lower(),
        )

    def _log_generation_start(
        self,
        art_style: str,
        character_name: str,
        character_age: int,
        gender: Gender,
        num_images: int,
    ):
        logger.debug(
            "Generating character reference poses",
            art_style=art_style,
            character_name=character_name,
            character_age=character_age,
            gender=gender,
            num_reference_images=num_images,
        )

    def _process_generation_response(
        self,
        response,
        art_style: str,
        character_name: str,
        gender: Gender,
    ) -> Optional[str]:
        generated_image = None
        response_text = ""

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                response_text += part.text
            elif part.inline_data is not None:
                image_data = part.inline_data.data
                generated_image = Image.open(io.BytesIO(image_data))

                if temp_path := save_image_to_temp(
                    generated_image,
                    suffix=Suffix.png,
                ):
                    return temp_path

        logger.warning(
            "No character image generated - text response only",
            response_text=response_text[:200],
        )
        return None
