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

        self.image_generator = ImageGenerator(client=client, model=model)
        self.text_processor = TextProcessor(client=client, model=model)

    def generate_story(
        self,
        story_template: StoryTemplate,
        seed_images: Optional[List] = None,
        metadata: Optional[StoryMetadata] = None,
        system_prompt: Optional[str] = None,
        character_name: Optional[str] = None,
        character_age: Optional[int] = None,
        character_gender: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[GeneratedPage]:
        results = []

        try:
            processed_texts = self.text_processor.process_pages(  # TODO: make sure metadata is passed correctly
                metadata=metadata,
                pages=story_template.pages,
                system_prompt=system_prompt,
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
                language=language,
            )

            for page_number, page in enumerate(story_template.pages):
                logger.info(
                    "Generating content for page",
                    page_number=page_number + 1,
                    title=page.title,
                )

                text = (
                    processed_texts.get(page_number, page.story_text)
                    if processed_texts
                    else page.story_text
                )

                image_path = None
                if seed_images or metadata:
                    logger.info(f"Generating image with {len(seed_images) if seed_images else 0} seed images")
                    if metadata:
                        logger.info(f"Metadata: name={getattr(metadata, 'character_name', 'N/A')}, age={getattr(metadata, 'age', 'N/A')}, gender={getattr(metadata, 'gender', 'N/A')}")

                    previous_pages = (
                        [
                            {
                                "title": p.title,
                                "text": p.text,
                                "illustration_prompt": p.illustration_prompt,
                            }
                            for p in results
                        ]
                        if results
                        else None
                    )

                    previous_images = (
                        [p.image_path for p in results if p.image_path]
                        if results
                        else None
                    )

                    image_path = self.image_generator.generate(
                        seed_images=seed_images,
                        illustration_prompt=page.illustration_prompt,
                        page_title=page.title,
                        story_text=text,
                        metadata=metadata,
                        system_prompt=system_prompt,
                        previous_pages=previous_pages,
                        previous_images=previous_images,
                    )

                # Create GeneratedPage
                generated_page = GeneratedPage(
                    page_number=page_number + 1,
                    title=page.title,
                    text=text,
                    illustration_prompt=page.illustration_prompt,
                    image_path=image_path,
                )

                results.append(generated_page)

            logger.info(f"Successfully generated {len(results)} pages")
            return results

        except Exception as e:
            logger.error(f"Failed to generate story: {str(e)}")
            logger.error(traceback.format_exc())
            return []
