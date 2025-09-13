import json
from google import genai
from google.genai import types
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator
from app.utils.schemas import Gender, PageData, PersonalizedStoryBook
from jinja2 import Template


class TextPersonalizer(BaseAIGenerator):
    def __init__(self, client: genai.Client, model: str):
        super().__init__(client, model)

    def generate(self, *args, **kwargs):
        return self.personalize(*args, **kwargs)

    def personalize_all_pages(
        self,
        pages_data: list[PageData],
        character_name: str,
        character_age: int,
        character_gender: Gender,
    ) -> PersonalizedStoryBook | None:
        """Personalize all pages at once for better story continuity."""
        return self._personalize_all_impl(
            pages_data=pages_data,
            character_name=character_name,
            character_age=character_age,
            character_gender=character_gender,
        )

    def personalize(
        self,
        text: str,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        previous_pages: list[PageData] | None = None,
    ) -> str:
        return self._personalize_impl(
            text=text,
            character_name=character_name,
            character_age=character_age,
            character_gender=character_gender,
            previous_pages=previous_pages,
        )

    def _personalize_all_impl(
        self,
        pages_data: list[PageData],
        character_name: str,
        character_age: int,
        character_gender: Gender,
    ) -> PersonalizedStoryBook | None:
        """Personalize all pages using batch processing for better continuity."""

        template: Template = self.env.get_template("text_personalization.j2")
        prompt = template.render(
            character_name=character_name,
            character_age=character_age,
            character_gender=character_gender.lower(),
            is_batch_processing=True,
            pages_data=pages_data,
        )

        # Use a text-only model for JSON schema support (image models don't support JSON mode)
        # Note: We temporarily use a different client for JSON schema generation
        text_model = "gemini-2.0-flash-exp"  # This model supports JSON mode

        try:
            response = self.client.models.generate_content(
                model=text_model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PersonalizedStoryBook,
                ),
            )
        except Exception as json_error:
            logger.warning(
                f"JSON schema generation failed with {text_model}, falling back to text parsing",
                error=str(json_error)
            )
            # Fall back to regular generation without schema
            response = self._generate_content(contents=[prompt])

        if not response or not response.candidates:
            logger.warning("No response from AI for batch personalization")
            return None

        try:
            # Try to use parsed response first (if schema was used)
            if hasattr(response, 'parsed') and response.parsed:
                # response.parsed should already be validated by Gemini's schema
                personalized_book = PersonalizedStoryBook.model_validate(response.parsed)
                logger.info(
                    "Successfully personalized all pages using response schema",
                    total_pages=len(pages_data),
                    character_name=character_name,
                    character_age=character_age,
                )
                return personalized_book
            else:
                # Fallback: extract JSON from text response
                response_text = ""
                for part in response.candidates[0].content.parts:
                    if part.text is not None:
                        response_text += part.text.strip()

                # Look for JSON in the response text
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1

                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    parsed_data = json.loads(json_text)
                    personalized_book = PersonalizedStoryBook.model_validate(parsed_data)
                    logger.info(
                        "Successfully personalized all pages using JSON parsing",
                        total_pages=len(pages_data),
                        character_name=character_name,
                        character_age=character_age,
                    )
                    return personalized_book
                else:
                    logger.warning(
                        "No JSON found in batch personalization response",
                        response_preview=response_text[:200],
                        character_name=character_name,
                    )
                    return None

        except Exception as e:
            logger.warning(
                "Failed to create PersonalizedStoryBook from response, falling back to individual processing",
                error=str(e),
                character_name=character_name,
            )
            return None

    def _personalize_impl(
        self,
        text: str,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        previous_pages: list[PageData] | None = None,
    ) -> str | None:
        """Personalize a single page with context from previous pages."""

        template: Template = self.env.get_template("text_personalization.j2")
        prompt = template.render(
            character_name=character_name,
            character_age=character_age,
            character_gender=character_gender.lower(),
            is_batch_processing=False,
            story_text=text,
            previous_pages=previous_pages,
        )

        response = self._generate_content([prompt])

        if (
            not response
            or not response.candidates
            or not response.candidates[0].content.parts
        ):
            personalized_text = None

        personalized_text = None
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                personalized_text = part.text.strip()

        if personalized_text:
            logger.info(
                "Successfully personalized story text",
                original_length=len(text),
                personalized_length=len(personalized_text),
                had_previous_context=previous_pages is not None,
                character_name=character_name,
                character_age=character_age,
            )
            return personalized_text
        else:
            logger.warning(
                "AI personalization failed, falling back to simple name replacement",
                character_name=character_name,
                had_previous_context=previous_pages is not None,
            )
            return text.replace("hero", character_name)
