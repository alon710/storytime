"""Text processing component for StoryTime application using text_personalization.j2 template."""

import json
from typing import Optional, List, Dict
from google import genai
from google.genai import types
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator
from app.utils.schemas import StoryMetadata, PageData


class TextProcessor(BaseAIGenerator):
    """AI-powered text processor for personalizing story content."""

    def __init__(self, client: genai.Client, model: str):
        """Initialize the text processor.

        Args:
            client: Google Gemini API client
            model: Model name to use for generation
        """
        super().__init__(client, model)

    def generate(self, *args, **kwargs):
        """Abstract method implementation."""
        return self.process_pages(*args, **kwargs)

    def process_pages(
        self,
        pages: List[PageData],
        metadata: Optional[StoryMetadata] = None,
        system_prompt: Optional[str] = None,
        character_name: Optional[str] = None,
        character_age: Optional[int] = None,
        character_gender: Optional[str] = None,
    ) -> Dict[int, str]:
        """Process story pages using text_personalization.j2 template for better narrative flow.

        Args:
            pages: List of PageData objects with story content
            metadata: Optional metadata with instructions
            system_prompt: Optional system prompt for generation
            character_name: Name of the main character
            character_age: Age of the character
            character_gender: Gender of the character

        Returns:
            Dictionary mapping page index to processed text
        """
        try:
            # Use the text_personalization.j2 template for batch processing
            template = self.env.get_template("text_personalization.j2")

            # Add page indices and total count for better context
            pages_with_context = []
            for idx, page in enumerate(pages):
                page_dict = {
                    "title": page.title,
                    "story_text": page.story_text,
                    "illustration_prompt": page.illustration_prompt,
                    "page_index": idx + 1,
                    "total_pages": len(pages),
                    "is_first": idx == 0,
                    "is_last": idx == len(pages) - 1
                }
                pages_with_context.append(page_dict)

            prompt = template.render(
                character_name=character_name or "Hero",
                character_age=character_age or 5,
                character_gender=character_gender or "child",
                is_batch_processing=True,
                pages_data=pages_with_context,
            )

            # Add any additional system instructions
            if system_prompt:
                prompt = f"{system_prompt}\n\n{prompt}"

            # Use text-only model for JSON schema support
            text_model = "gemini-2.0-flash-exp"

            # Generate personalized text with JSON schema
            response = self.client.models.generate_content(
                model=text_model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192,
                ),
            )

            if not response or not response.candidates:
                logger.warning("No response from AI for text processing")
                return {}

            processed_texts = {}

            try:
                # Parse JSON response
                response_text = ""
                for part in response.candidates[0].content.parts:
                    if part.text is not None:
                        response_text += part.text.strip()

                # Find and parse JSON
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1

                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    parsed_data = json.loads(json_text)

                    # Extract personalized pages
                    if "personalized_pages" in parsed_data:
                        for page_data in parsed_data["personalized_pages"]:
                            page_num = (
                                page_data.get("page_number", 0) - 1
                            )  # Convert to 0-indexed
                            personalized_text = page_data.get("personalized_text", "")
                            if page_num >= 0 and personalized_text:
                                processed_texts[page_num] = personalized_text

                    logger.info(
                        f"Successfully personalized {len(processed_texts)} pages with narrative flow"
                    )
                    return processed_texts

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {str(e)}")
                # Fallback: process pages individually
                return self._process_pages_individually(
                    pages,
                    character_name,
                    character_age,
                    character_gender,
                    system_prompt,
                )

        except Exception as e:
            logger.error(f"Failed to process text: {str(e)}")
            return {}

        return {}

    def _process_pages_individually(
        self,
        pages: List[PageData],
        character_name: str,
        character_age: int,
        character_gender: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[int, str]:
        """Fallback method to process pages individually with context."""
        processed_texts = {}
        previous_pages = []

        for i, page in enumerate(pages):
            try:
                # Use the template for single page processing
                template = self.env.get_template("text_personalization.j2")
                prompt = template.render(
                    character_name=character_name,
                    character_age=character_age,
                    character_gender=character_gender,
                    is_batch_processing=False,
                    story_text=page.story_text,
                    previous_pages=previous_pages,  # Pass all previous pages for context
                )

                if system_prompt:
                    prompt = f"{system_prompt}\n\n{prompt}"

                response = self._generate_content([prompt])

                if (
                    response
                    and response.candidates
                    and response.candidates[0].content.parts
                ):
                    for part in response.candidates[0].content.parts:
                        if part.text is not None:
                            personalized_text = part.text.strip()
                            processed_texts[i] = personalized_text
                            # Add to previous pages for next iteration
                            previous_pages.append(
                                {"title": page.title, "story_text": personalized_text}
                            )
                            break

            except Exception as e:
                logger.warning(f"Failed to process page {i}: {str(e)}")
                # Use original text as fallback
                processed_texts[i] = page.story_text.replace(
                    "Hero", character_name
                ).replace("hero", character_name)
                previous_pages.append(
                    {"title": page.title, "story_text": processed_texts[i]}
                )

        return processed_texts
