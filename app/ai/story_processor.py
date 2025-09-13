"""Main orchestrator for StoryTime story generation."""

import traceback
from typing import Optional, List

from google import genai
from app.utils.schemas import StoryMetadata, StoryTemplate, GeneratedPage
from app.utils.settings import settings
from app.ai.image_generator import ImageGenerator
from app.ai.text_processor import TextProcessor

from app.utils.logger import logger


class StoryProcessor:
    def __init__(self):
        client = genai.Client(api_key=settings.google_api_key)
        model = settings.model

        self.image_generator = ImageGenerator(client, model)
        self.text_processor = TextProcessor(client, model)

    def generate_story(
        self,
        story_template: StoryTemplate,
        seed_images: Optional[List] = None,
        metadata: Optional[StoryMetadata] = None,
        system_prompt: Optional[str] = None,
    ) -> List[GeneratedPage]:
        """Generate story with text and images.

        Args:
            story_template: Template with pages to generate
            seed_images: Optional seed images for visual reference
            metadata: Optional metadata with instructions
            system_prompt: Optional system prompt for generation

        Returns:
            List of GeneratedPage objects with content and images
        """
        results = []

        try:
            # Process text for all pages
            processed_texts = self.text_processor.process_pages(
                pages=story_template.pages,
                metadata=metadata,
                system_prompt=system_prompt
            )

            # Generate images for each page
            for i, page in enumerate(story_template.pages):
                logger.info(f"Generating content for page {i + 1}: {page.title}")

                # Get processed text or use original
                text = processed_texts.get(i, page.story_text) if processed_texts else page.story_text

                # Generate image
                image_path = None
                if seed_images or metadata:
                    # Collect previous pages context
                    previous_pages = [
                        {"title": p.title, "text": p.text, "illustration_prompt": p.illustration_prompt}
                        for p in results
                    ] if results else None

                    # Collect previous generated images for visual consistency
                    previous_images = [
                        p.image_path for p in results if p.image_path
                    ] if results else None

                    image_path = self.image_generator.generate(
                        seed_images=seed_images,
                        illustration_prompt=page.illustration_prompt,
                        page_title=page.title,
                        story_text=text,
                        metadata=metadata,
                        system_prompt=system_prompt,
                        previous_pages=previous_pages,
                        previous_images=previous_images
                    )

                # Create GeneratedPage
                generated_page = GeneratedPage(
                    page_number=i + 1,
                    title=page.title,
                    text=text,
                    illustration_prompt=page.illustration_prompt,
                    image_path=image_path
                )

                results.append(generated_page)

            logger.info(f"Successfully generated {len(results)} pages")
            return results

        except Exception as e:
            logger.error(f"Failed to generate story: {str(e)}")
            logger.error(traceback.format_exc())
            return []