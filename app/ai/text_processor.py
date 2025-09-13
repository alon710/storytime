"""Text processing component for StoryTime application."""

from typing import Optional, List, Dict
from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator
from app.utils.schemas import StoryMetadata, PageData


class TextProcessor(BaseAIGenerator):
    """AI-powered text processor for story content."""

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
        system_prompt: Optional[str] = None
    ) -> Dict[int, str]:
        """Process story pages with optional metadata and instructions.

        Args:
            pages: List of PageData objects with story content
            metadata: Optional metadata with instructions
            system_prompt: Optional system prompt for generation

        Returns:
            Dictionary mapping page index to processed text
        """
        if not metadata and not system_prompt:
            # No processing needed if no metadata or system prompt
            return {}

        try:
            # Build prompt for text processing
            prompt_parts = []

            if system_prompt:
                prompt_parts.append(f"System Instructions: {system_prompt}")

            if metadata:
                if metadata.title:
                    prompt_parts.append(f"Story Title: {metadata.title}")
                if metadata.description:
                    prompt_parts.append(f"Description: {metadata.description}")
                if metadata.instructions:
                    prompt_parts.append(f"Special Instructions: {metadata.instructions}")
                if metadata.additional_context:
                    prompt_parts.append(f"Additional Context: {metadata.additional_context}")

            prompt_parts.append("\nProcess the following story pages according to the instructions above:")
            prompt_parts.append("Maintain story continuity and consistency across all pages.")
            prompt_parts.append("Return the processed text for each page.\n")

            for i, page in enumerate(pages):
                prompt_parts.append(f"\nPage {i + 1} - {page.title}:")
                prompt_parts.append(f"Original: {page.story_text}")

            prompt = "\n".join(prompt_parts)

            # Generate processed text
            response = self._generate_content([prompt])

            if not response or not response.candidates:
                logger.warning("No response from AI for text processing")
                return {}

            # Parse response and extract processed texts
            processed_texts = {}
            response_text = ""

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    response_text += part.text.strip()

            # Simple parsing - look for page indicators
            lines = response_text.split("\n")
            current_page = None
            current_text = []

            for line in lines:
                if "Page" in line and (":" in line or "-" in line):
                    # Save previous page if exists
                    if current_page is not None and current_text:
                        processed_texts[current_page] = " ".join(current_text).strip()
                    # Extract page number
                    try:
                        page_num = int(''.join(filter(str.isdigit, line.split(":")[0])))
                        current_page = page_num - 1  # Convert to 0-indexed
                        current_text = []
                    except (ValueError, IndexError):
                        continue
                elif current_page is not None and line.strip():
                    current_text.append(line.strip())

            # Save last page
            if current_page is not None and current_text:
                processed_texts[current_page] = " ".join(current_text).strip()

            logger.info(f"Successfully processed {len(processed_texts)} pages")
            return processed_texts

        except Exception as e:
            logger.error(f"Failed to process text: {str(e)}")
            return {}