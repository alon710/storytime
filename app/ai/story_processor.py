"""Main orchestrator for StoryTime storybook generation."""

import time
import traceback
from typing import Optional

from google import genai
from app.utils.schemas import Gender, PageData, PersonalizedStoryBook, PersonalizedPage, GeneratedPage
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

    def generate_preview(
        self,
        pages_data: list[PageData],
        character_images,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        progress_bar=None,
    ) -> list[GeneratedPage]:
        """Generate preview with personalized text and images for editing."""
        results = []

        try:
            # Personalize all text first for better story continuity
            if progress_bar:
                progress_bar.progress(5, "Personalizing story text...")

            personalized_book = self.text_personalizer.personalize_all_pages(
                pages_data=pages_data,
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
            )

            if not personalized_book:
                logger.warning("Batch personalization failed, will use individual personalization")

            # Generate images
            image_paths = self._generate_all_images(
                pages_data,
                character_images,
                character_name,
                character_age,
                character_gender,
                progress_bar,
                personalized_book,
            )

            # Create GeneratedPage objects
            for i, (page_data, image_path) in enumerate(zip(pages_data, image_paths)):
                personalized_text = page_data.story_text  # fallback
                if personalized_book and i < len(personalized_book.personalized_pages):
                    personalized_text = personalized_book.personalized_pages[i].personalized_text

                results.append(GeneratedPage(
                    page_data=page_data,
                    personalized_text=personalized_text,
                    image_path=image_path,
                ))

            if progress_bar:
                progress_bar.progress(100, "Preview ready!")

            return results

        except Exception as e:
            logger.error(f"Failed to generate preview: {str(e)}")
            if progress_bar:
                progress_bar.progress(0, f"Error: {str(e)}")
            return []

    def create_pdf_from_preview(
        self,
        generated_pages: list[GeneratedPage],
        character_name: str,
        character_age: int,
        character_gender: Gender,
    ) -> Optional[str]:
        """Create PDF from edited generated pages."""
        try:
            # Convert GeneratedPage objects back to the format expected by PDFBuilder
            pages_data = [page.page_data for page in generated_pages]
            image_paths = [page.image_path for page in generated_pages]

            # Create a personalized book with edited text
            personalized_pages = []
            for i, generated_page in enumerate(generated_pages):
                final_text = generated_page.edited_text if generated_page.edited_text else generated_page.personalized_text
                personalized_pages.append(PersonalizedPage(
                    page_number=i + 1,
                    title=generated_page.page_data.title,
                    personalized_text=final_text,
                ))

            personalized_book = PersonalizedStoryBook(personalized_pages=personalized_pages)

            return self.pdf_builder.create_book(
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
                pages_data=pages_data,
                image_paths=image_paths,
                personalized_book=personalized_book,
            )
        except Exception as e:
            logger.error(f"Failed to create PDF from preview: {str(e)}")
            return None

    def create_pdf_booklet(
        self,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        pages_data: list[PageData],
        image_paths,
        personalized_book: PersonalizedStoryBook | None = None,
    ) -> Optional[str]:
        return self.pdf_builder.create_book(
            character_name=character_name,
            character_age=character_age,
            character_gender=character_gender,
            pages_data=pages_data,
            image_paths=image_paths,
            personalized_book=personalized_book,
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
            # Personalize all text first for better story continuity
            if progress_bar:
                progress_bar.progress(5, "Personalizing story text...")

            personalized_book = self.text_personalizer.personalize_all_pages(
                pages_data=pages_data,
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
            )

            if not personalized_book:
                logger.warning("Batch personalization failed, will use individual personalization")

            image_paths = self._generate_all_images(
                pages_data,
                character_images,
                character_name,
                character_age,
                character_gender,
                progress_bar,
                personalized_book,
            )

            if not image_paths:
                return results

            if progress_bar:
                progress_bar.progress(90, "Creating PDF booklet...")

            pdf_path = self.create_pdf_booklet(
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
                pages_data=pages_data,
                image_paths=image_paths,
                personalized_book=personalized_book,
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
        personalized_book: PersonalizedStoryBook | None = None,
    ):
        if progress_bar:
            progress_bar.progress(10, "Generating illustrations...")

        image_paths = []
        for i, page_data in enumerate(pages_data):
            if progress_bar:
                progress = 10 + (75 * (i + 1) / len(pages_data))
                progress_bar.progress(
                    int(progress), f"Generating image {i + 1}/{len(pages_data)}..."
                )

            previous_pages = (
                [page.model_dump() for page in pages_data[:i]] if i > 0 else None
            )
            previous_images = image_paths[:i] if i > 0 else None

            logger.info(
                "Generating image with context",
                page_number=i + 1,
                total_pages=len(pages_data),
                page_title=page_data.title,
                previous_pages_count=len(previous_pages) if previous_pages else 0,
                previous_images_count=len(previous_images) if previous_images else 0,
            )

            # Use personalized text if available, otherwise use original
            story_text_for_image = page_data.story_text
            if personalized_book and i < len(personalized_book.personalized_pages):
                story_text_for_image = personalized_book.personalized_pages[i].personalized_text

            image_path = self.image_generator.generate(
                character_images,
                character_name,
                character_age,
                character_gender,
                page_data.illustration_prompt,
                page_data.title,
                story_text_for_image,
                previous_pages,
                previous_images,
            )

            image_paths.append(image_path)

        return image_paths
