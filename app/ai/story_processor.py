"""Main orchestrator for StoryTime storybook generation."""

import time
import traceback
from typing import Optional

from google import genai
from app.utils.schemas import Gender, PageData
from app.utils.settings import settings
from app.ai.character_image_generator import CharacterImageGenerator
from app.ai.text_personalizer import TextPersonalizer
from app.pdf.pdf_builder import PDFBuilder

from app.utils.logger import logger


class StoryProcessor:
    def __init__(self):
        client = genai.Client(api_key=settings.google_api_key)
        model = settings.model

        self.image_generator = CharacterImageGenerator(client, model)
        self.text_personalizer = TextPersonalizer(client, model)
        self.pdf_builder = PDFBuilder(self.text_personalizer)

    def create_pdf_booklet(
        self,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        pages_data: list[PageData],
        image_paths,
    ) -> Optional[str]:
        return self.pdf_builder.create_book(
            character_name=character_name,
            character_age=character_age,
            character_gender=character_gender,
            pages_data=pages_data,
            image_paths=image_paths,
        )

    def process_story(
        self,
        pages_data: list[PageData],
        character_images,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        progress_bar=None,
    ) -> dict:
        results = {
            "success": False,
            "pages_processed": 0,
            "error": None,
            "pdf_path": None,
            "processing_time": 0,
        }

        start_time = time.time()

        try:
            image_paths = self._generate_all_images(
                pages_data,
                character_images,
                character_name,
                character_age,
                character_gender,
                progress_bar,
            )

            if not image_paths:
                return results

            if progress_bar:
                progress_bar.progress(85, "Creating PDF booklet...")

            pdf_path = self.create_pdf_booklet(
                character_name,
                character_age,
                character_gender,
                pages_data,
                image_paths,
            )

            if progress_bar:
                progress_bar.progress(100, "Complete!")

            results.update(
                {
                    "success": True,
                    "pdf_path": pdf_path,
                    "pages_processed": len(pages_data),
                    "processing_time": time.time() - start_time,
                }
            )

        except Exception as e:
            error_details = traceback.format_exc()
            results["error"] = error_details
            if progress_bar:
                progress_bar.progress(0, f"Error: {str(e)}")

        return results

    def _generate_all_images(
        self,
        pages_data,
        character_images,
        character_name,
        character_age,
        character_gender,
        progress_bar,
    ):
        if progress_bar:
            progress_bar.progress(30, "Generating illustrations...")

        image_paths = []
        for i, page_data in enumerate(pages_data):
            if progress_bar:
                progress = 10 + (70 * (i + 1) / len(pages_data))
                progress_bar.progress(
                    int(progress), f"Generating image {i + 1}/{len(pages_data)}..."
                )

            previous_pages = pages_data[:i] if i > 0 else None
            previous_images = image_paths[:i] if i > 0 else None

            logger.info(
                "Generating image with context",
                page_number=i + 1,
                total_pages=len(pages_data),
                page_title=page_data.title,
                previous_pages_count=len(previous_pages) if previous_pages else 0,
                previous_images_count=len(previous_images) if previous_images else 0,
            )

            image_path = self.image_generator.generate(
                character_images,
                character_name,
                character_age,
                character_gender,
                page_data.illustration_prompt,
                page_data.title,
                page_data.story_text,
                previous_pages,
                previous_images,
            )

            image_paths.append(image_path)

        return image_paths
