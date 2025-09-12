"""Text personalization module for StoryTime."""

from google import genai
from google.genai import types
from logger import logger


class TextPersonalizer:
    """Handles AI-powered text personalization for age and gender-appropriate language."""

    def __init__(self, client: genai.Client, model: str):
        """Initialize personalizer with GenAI client and model."""
        self.client = client
        self.model = model

    def personalize(
        self, text: str, character_name: str, character_age: int, character_gender: str
    ) -> str:
        """Personalize story text for age and gender-appropriate language."""
        try:
            personalization_prompt = f"""
            Rewrite this children's story text:
            
            Original: "{text}"
            
            Requirements:
            - Replace "hero" with {character_name}
            - Use language appropriate for {character_age}-year-old {character_gender.lower()} But keep it as similar as possible to the original text
            - Keep same story events and meaning
            - Simple, engaging vocabulary for ages {max(2, character_age - 2)}-{character_age + 2}
            - Warm, child-friendly tone
            - Same approximate length
            - Use appropriate pronouns
            
            Return only the rewritten text.
            """

            response = self.client.models.generate_content(
                model=self.model,
                contents=[personalization_prompt],
                config=types.GenerateContentConfig(response_modalities=["Text"]),
            )

            if (
                response
                and response.candidates
                and response.candidates[0].content.parts
            ):
                personalized_text = response.candidates[0].content.parts[0].text.strip()
                logger.info(
                    "Successfully personalized story text",
                    extra={
                        "original_length": len(text),
                        "personalized_length": len(personalized_text),
                    },
                )
                return personalized_text
            else:
                logger.warning(
                    "AI personalization failed, falling back to simple name replacement"
                )
                return self._simple_replacement(text, character_name)

        except Exception as e:
            logger.error(
                "AI personalization failed", extra={"error": str(e)}, exc_info=True
            )
            return self._simple_replacement(text, character_name)

    def _simple_replacement(self, text: str, character_name: str) -> str:
        """Fallback method for simple hero-to-name replacement."""
        return text.replace("hero", character_name).replace("Hero", character_name)
