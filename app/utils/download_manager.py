"""Download manager for creating story archives."""

import json
import os
import tempfile
import zipfile
from typing import List, Optional

from app.utils.logger import logger
from app.utils.schemas import GeneratedPage, StoryMetadata, StoryTemplate


class DownloadManager:
    @staticmethod
    def create_story_text(pages: List[GeneratedPage]) -> str:
        story_lines = []

        for page in pages:
            story_lines.append(f"Page {page.page_number}: {page.title}")
            story_lines.append("-" * 40)
            text = page.edited_text if page.edited_text else page.text
            story_lines.append(text)
            story_lines.append("\n")

        return "\n".join(story_lines)

    @staticmethod
    def create_metadata_dict(
        pages: List[GeneratedPage],
        story_title: str,
        metadata: StoryMetadata,
        template: Optional[StoryTemplate] = None,
    ) -> dict:
        """Create metadata dictionary for the story."""
        metadata_dict = {
            "story_title": story_title,
            "total_pages": len(pages),
            "language": metadata.language.value,
            "character": {
                "name": metadata.character_name,
                "age": metadata.age,
                "gender": metadata.gender.value,
            },
            "art_style": metadata.art_style.value,
        }

        if metadata.instructions:
            metadata_dict["instructions"] = metadata.instructions

        if template:
            metadata_dict["template_name"] = template.name
            metadata_dict["template_description"] = template.description

        metadata_dict["pages"] = []
        for page in pages:
            page_info = {
                "page_number": page.page_number,
                "title": page.title,
                "illustration_prompt": page.illustration_prompt,
                "has_image": bool(page.image_path and os.path.exists(page.image_path)),
            }
            metadata_dict["pages"].append(page_info)

        return metadata_dict

    @classmethod
    def create_archive(
        cls,
        pages: List[GeneratedPage],
        story_title: str,
        metadata: StoryMetadata,
        template: Optional[StoryTemplate] = None,
    ) -> Optional[str]:
        """Create a zip archive containing story content, metadata, and images."""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".zip", prefix=f"{story_title}_", delete=False
            ) as tmp_zip:
                zip_path = tmp_zip.name

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                story_text = cls.create_story_text(pages)
                zipf.writestr("story.txt", story_text.encode("utf-8"))
                logger.info("Added story.txt to archive")

                metadata_dict = cls.create_metadata_dict(
                    pages=pages,
                    story_title=story_title,
                    metadata=metadata,
                    template=template,
                )
                metadata_json = json.dumps(metadata_dict, indent=2, ensure_ascii=False)
                zipf.writestr("metadata.json", metadata_json.encode("utf-8"))
                logger.info("Added metadata.json to archive")

                for page in pages:
                    if page.image_path and os.path.exists(page.image_path):
                        image_filename = f"page_{page.page_number:02d}.png"
                        zipf.write(page.image_path, image_filename)
                        logger.info(f"Added {image_filename} to archive")
                    else:
                        logger.warning(
                            f"Image not found for page {page.page_number}",
                            image_path=page.image_path,
                        )

            logger.info(
                "Successfully created story archive",
                zip_path=zip_path,
                size_kb=os.path.getsize(zip_path) / 1024,
            )
            return zip_path

        except Exception as e:
            logger.error(f"Failed to create archive: {str(e)}")
            return None
