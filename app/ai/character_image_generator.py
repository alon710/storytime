import io
from typing import Optional
from PIL import Image
from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator
from app.utils.schemas import Gender, Suffix
from app.utils.temp_file import save_image_to_temp
from jinja2 import Template


class CharacterImageGenerator(BaseAIGenerator):
    def __init__(self, client: genai.Client, model: str):
        super().__init__(client, model)

    def generate(
        self,
        character_images,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        illustration_prompt: str,
        book_title: str,
        page_title: str,
        story_text: str = "",
        previous_pages: list[dict] | None = None,
        previous_images: list[str] | None = None,
    ) -> Optional[str]:
        return self._generate_character_image(
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

    def _generate_character_image(
        self,
        character_images,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        illustration_prompt: str,
        book_title: str,
        page_title: str,
        story_text: str = "",
        previous_pages: list[dict] | None = None,
        previous_images: list[str] | None = None,
    ) -> Optional[str]:
        character_image_inputs = [Image.open(fp=img) for img in character_images]
        previous_image_inputs = []

        if previous_images:
            recent_images = (
                previous_images[-3:] if len(previous_images) > 3 else previous_images
            )
            previous_image_inputs = [Image.open(img_path) for img_path in recent_images]

        system_prompt = self._build_system_prompt(
            book_title=book_title,
            page_title=page_title,
            character_name=character_name,
            character_age=character_age,
            character_gender=character_gender,
            num_character_images=len(character_image_inputs),
            illustration_prompt=illustration_prompt,
            story_text=story_text,
            previous_pages=previous_pages,
            num_previous_images=len(previous_image_inputs),
        )

        contents = (
            [system_prompt, illustration_prompt]
            + character_image_inputs
            + previous_image_inputs
        )

        if not (response := self._generate_content(contents, ["Text", "Image"])):
            return None

        generated_image = None
        response_text = ""

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                response_text += part.text
            elif part.inline_data is not None:
                image_data = part.inline_data.data
                generated_image = Image.open(io.BytesIO(image_data))

                if temp_path := save_image_to_temp(
                    image=generated_image,
                    suffix=Suffix.png,
                ):
                    logger.info(
                        "Successfully generated image for page",
                        page_title=page_title,
                    )
                    return temp_path

        logger.warning(
            "No image generated for page - text response only",
            page_title=page_title,
        )
        return None

    def _build_system_prompt(
        self,
        book_title: str,
        page_title: str,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        num_character_images: int,
        illustration_prompt: str,
        story_text: str,
        previous_pages: list[dict] | None,
        num_previous_images: int,
    ) -> str:
        template: Template = self.env.get_template("image_generation.j2")
        return template.render(
            book_title=book_title,
            page_title=page_title,
            character_name=character_name,
            character_age=character_age,
            character_gender=character_gender.lower(),
            num_character_images=num_character_images,
            illustration_prompt=illustration_prompt,
            story_text=story_text,
            previous_pages=previous_pages,
            num_previous_images=num_previous_images,
        )
