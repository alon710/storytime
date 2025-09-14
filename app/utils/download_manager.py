"""Download manager for creating story archives."""

import json
import os
import re
import tempfile
import zipfile
from typing import List, Optional

from app.utils.logger import logger
from app.utils.schemas import GeneratedPage, StoryMetadata, StoryTemplate


class DownloadManager:
    """Manages creation of downloadable archives containing story content."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = sanitized.strip('. ')
        return sanitized[:255] if sanitized else "story"

    @staticmethod
    def create_story_text(pages: List[GeneratedPage]) -> str:
        """Combine all pages into a single story text."""
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
        character_name: Optional[str] = None,
        character_age: Optional[int] = None,
        character_gender: Optional[str] = None,
        metadata: Optional[StoryMetadata] = None,
        template: Optional[StoryTemplate] = None,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """Create metadata dictionary for the story."""
        metadata_dict = {
            "story_title": story_title,
            "total_pages": len(pages),
            "character": {
                "name": character_name or (metadata.character_name if metadata else "Unknown"),
                "age": character_age or (metadata.age if metadata else None),
                "gender": character_gender or (metadata.gender if metadata else None),
            },
        }

        if metadata:
            metadata_dict["art_style"] = metadata.art_style.value if metadata.art_style else None
            metadata_dict["instructions"] = metadata.instructions

        if system_prompt:
            metadata_dict["system_prompt"] = system_prompt

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
        character_name: Optional[str] = None,
        character_age: Optional[int] = None,
        character_gender: Optional[str] = None,
        metadata: Optional[StoryMetadata] = None,
        template: Optional[StoryTemplate] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """Create a zip archive containing story content, metadata, and images."""
        try:
            sanitized_title = cls.sanitize_filename(story_title)

            with tempfile.NamedTemporaryFile(
                suffix=".zip",
                prefix=f"{sanitized_title}_",
                delete=False
            ) as tmp_zip:
                zip_path = tmp_zip.name

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                story_text = cls.create_story_text(pages)
                zipf.writestr("story.txt", story_text.encode('utf-8'))
                logger.info("Added story.txt to archive")

                metadata_dict = cls.create_metadata_dict(
                    pages=pages,
                    story_title=story_title,
                    character_name=character_name,
                    character_age=character_age,
                    character_gender=character_gender,
                    metadata=metadata,
                    template=template,
                    system_prompt=system_prompt,
                )
                metadata_json = json.dumps(metadata_dict, indent=2, ensure_ascii=False)
                zipf.writestr("metadata.json", metadata_json.encode('utf-8'))
                logger.info("Added metadata.json to archive")

                for page in pages:
                    if page.image_path and os.path.exists(page.image_path):
                        image_filename = f"page_{page.page_number:02d}.png"
                        zipf.write(page.image_path, image_filename)
                        logger.info(f"Added {image_filename} to archive")
                    else:
                        logger.warning(
                            f"Image not found for page {page.page_number}",
                            image_path=page.image_path
                        )

            logger.info(
                "Successfully created story archive",
                zip_path=zip_path,
                size_kb=os.path.getsize(zip_path) / 1024
            )
            return zip_path

        except Exception as e:
            logger.error(f"Failed to create archive: {str(e)}")
            return None