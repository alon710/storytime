"""Text personalization module for StoryTime."""

from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator


class TextPersonalizer(BaseAIGenerator):
    """Handles AI-powered text personalization for age and gender-appropriate language."""

    def __init__(self, client: genai.Client, model: str):
        """Initialize personalizer with GenAI client and model."""
        super().__init__(client, model)

    def generate(self, *args, **kwargs):
        """Main generation method - delegates to personalize."""
        return self.personalize(*args, **kwargs)

    def personalize(
        self,
        text: str,
        character_name: str,
        character_age: int,
        character_gender: str,
        previous_pages: list[dict] | None = None,
    ) -> str:
        """Personalize story text for age and gender-appropriate language."""
        result = self._with_error_handling(
            "text personalization",
            self._personalize_impl,
            text,
            character_name,
            character_age,
            character_gender,
            previous_pages
        )
        return result if result is not None else self._simple_replacement(text, character_name)

    def _personalize_impl(
        self,
        text: str,
        character_name: str,
        character_age: int,
        character_gender: str,
        previous_pages: list[dict] | None = None,
    ) -> str:
        # Build context from previous pages if provided
        context_info = ""
        if previous_pages:
            context_info = "\n\nPrevious story context for continuity:\n"
            for i, page in enumerate(previous_pages[-3:], 1):  # Last 3 pages only
                context_info += f"Page {i}: {page.get('title', '')} - {page.get('story_text', '')}\n"

            logger.info(
                "Including previous pages for text personalization continuity",
                extra={
                    "previous_pages_count": len(previous_pages),
                    "context_pages_used": min(3, len(previous_pages)),
                    "total_context_length": len(context_info),
                },
            )

        personalization_prompt = f"""
        Rewrite this children's story text:
        
        Original: "{text}"{context_info}
        
        Requirements:
        - Replace "hero" with {character_name}
        - Use language appropriate for {character_age}-year-old {character_gender.lower()} But keep it as similar as possible to the original text
        - Keep same story events and meaning
        - Simple, engaging vocabulary for ages {max(2, character_age - 2)}-{character_age + 2}
        - Warm, child-friendly tone
        - Same approximate length
        - Use appropriate pronouns
        - Maintain narrative consistency with previous pages
        
        Return only the rewritten text.
        """

        response = self._generate_content([personalization_prompt])
        if response is None:
            return self._simple_replacement(text, character_name)
            
        personalized_text = self._extract_text_response(response)
        if personalized_text:
            logger.info(
                "Successfully personalized story text",
                extra={
                    "original_length": len(text),
                    "personalized_length": len(personalized_text),
                    "had_previous_context": previous_pages is not None,
                    "character_name": character_name,
                    "character_age": character_age,
                },
            )
            return personalized_text
        else:
            logger.warning(
                "AI personalization failed, falling back to simple name replacement",
                extra={
                    "character_name": character_name,
                    "had_previous_context": previous_pages is not None,
                },
            )
            return self._simple_replacement(text, character_name)

    def _simple_replacement(self, text: str, character_name: str) -> str:
        """Fallback method for simple hero-to-name replacement."""
        return text.replace("hero", character_name).replace("Hero", character_name)
