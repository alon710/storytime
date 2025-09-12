"""Main orchestrator for StoryTime storybook generation."""

import os
import time

from google import genai
from config import settings
from image_generator import ImageGenerator
from text_personalizer import TextPersonalizer
from pdf_builder import PDFBuilder
from color_generator import ColorGenerator


class StoryProcessor:
    """Orchestrates the generation of illustrated children's books."""

    def __init__(self):
        """Initialize processor with specialized components."""
        os.environ["GEMINI_API_KEY"] = settings.google_api_key
        client = genai.Client(api_key=settings.google_api_key)
        model = settings.model

        self.image_generator = ImageGenerator(client, model)
        self.text_personalizer = TextPersonalizer(client, model)
        self.color_generator = ColorGenerator(client, model)
        self.pdf_builder = PDFBuilder(self.text_personalizer, self.color_generator)

    def generate_image_for_page(
        self,
        character_image,
        character_name: str,
        character_age: int,
        character_gender: str,
        illustration_prompt: str,
        book_title: str,
        page_title: str,
        story_text: str = "",
        previous_pages: list[dict] | None = None,
        previous_images: list[str] | None = None,
    ):
        """Generate illustration using image generator module."""
        return self.image_generator.generate(
            character_image,
            character_name,
            character_age,
            character_gender,
            illustration_prompt,
            book_title,
            page_title,
            story_text,
            previous_pages,
            previous_images,
        )

    def create_pdf_booklet(
        self,
        book_title: str,
        character_name: str,
        character_age: int,
        character_gender: str,
        pages_data: list[dict],
        image_paths,
        output_path: str,
    ) -> str:
        """Create illustrated PDF booklet using PDF builder module."""
        return self.pdf_builder.create_booklet(
            book_title,
            character_name,
            character_age,
            character_gender,
            pages_data,
            image_paths,
            output_path,
        )

    def process_story(
        self,
        pages_data: list[dict],
        character_image,
        character_name: str,
        character_age: int,
        character_gender: str,
        book_title: str,
        output_folder: str,
        progress_bar=None,
    ) -> dict:
        """Orchestrate complete illustrated storybook generation."""
        results = {
            "success": False,
            "pdf_path": None,
            "pages_processed": 0,
            "error": None,
            "processing_time": 0,
        }

        start_time = time.time()

        try:
            image_paths = self._generate_all_images(
                pages_data,
                character_image,
                character_name,
                character_age,
                character_gender,
                book_title,
                progress_bar,
            )

            if not image_paths:
                return results

            if progress_bar:
                progress_bar.progress(85, "Creating PDF booklet...")

            pdf_path = self.create_pdf_booklet(
                book_title,
                character_name,
                character_age,
                character_gender,
                pages_data,
                image_paths,
                output_folder,
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
            results["error"] = str(e)
            if progress_bar:
                progress_bar.progress(0, f"Error: {str(e)}")

        return results

    def _generate_all_images(
        self,
        pages_data,
        character_image,
        character_name,
        character_age,
        character_gender,
        book_title,
        progress_bar,
    ):
        """Generate images for all pages."""
        if progress_bar:
            progress_bar.progress(30, "Generating illustrations...")

        image_paths = []
        for i, page_data in enumerate(pages_data):
            if progress_bar:
                progress = 10 + (70 * (i + 1) / len(pages_data))
                progress_bar.progress(
                    int(progress), f"Generating image {i + 1}/{len(pages_data)}..."
                )

            # Pass previous pages and images as context for continuity
            previous_pages = pages_data[:i] if i > 0 else None
            previous_images = image_paths[:i] if i > 0 else None
            
            from logger import logger
            logger.info(
                "Generating image with context",
                extra={
                    "page_number": i + 1,
                    "total_pages": len(pages_data),
                    "page_title": page_data["title"],
                    "previous_pages_count": len(previous_pages) if previous_pages else 0,
                    "previous_images_count": len(previous_images) if previous_images else 0
                }
            )
            
            image_path = self.generate_image_for_page(
                character_image,
                character_name,
                character_age,
                character_gender,
                page_data["illustration_prompt"],
                book_title,
                page_data["title"],
                page_data.get("story_text", ""),
                previous_pages,
                previous_images,
            )

            if image_path is None:
                if progress_bar:
                    progress_bar.progress(0, "Error: Image generation failed")
                return None

            image_paths.append(image_path)

        return image_paths
