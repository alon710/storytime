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
        self, 
        text: str, 
        character_name: str, 
        character_age: int, 
        character_gender: str,
        language: str = "English"
    ) -> str:
        """Personalize and translate story text for age, gender, and language."""
        try:
            if language == "English":
                language_instruction = f"Write in {language} using age-appropriate vocabulary"
            else:
                language_instruction = f"Translate to {language} and adapt for native speakers"
            
            personalization_prompt = f"""
            Rewrite this children's story text:
            
            Original: "{text}"
            
            Requirements:
            - Replace "hero" with {character_name}
            - {language_instruction}
            - Use language appropriate for {character_age}-year-old {character_gender.lower()}
            - Keep same story events and meaning
            - Simple, engaging vocabulary for ages {max(2, character_age-2)}-{character_age+2}
            - Warm, child-friendly tone
            - Same approximate length
            - Use culturally appropriate expressions for {language}
            - Keep character names unchanged
            - Use appropriate pronouns and grammar for {language}
            
            Return only the rewritten text in {language}.
            """
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[personalization_prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["Text"]
                ),
            )
            
            if response and response.candidates and response.candidates[0].content.parts:
                personalized_text = response.candidates[0].content.parts[0].text.strip()
                logger.info("Successfully personalized story text", extra={
                    "original_length": len(text), 
                    "personalized_length": len(personalized_text)
                })
                return personalized_text
            else:
                logger.warning("AI personalization failed, falling back to simple name replacement")
                return self._simple_replacement(text, character_name)
                
        except Exception as e:
            logger.error("AI personalization failed", extra={"error": str(e)}, exc_info=True)
            return self._simple_replacement(text, character_name)
    
    def _simple_replacement(self, text: str, character_name: str) -> str:
        """Fallback method for simple hero-to-name replacement."""
        return text.replace("hero", character_name).replace("Hero", character_name)