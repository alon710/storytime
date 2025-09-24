import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from PIL import Image
from .base import BaseTool
from .narrator import StoryBook


class StorageTool(BaseTool):
    def __init__(self, model: str, storage_path: str = "./sessions"):
        super().__init__(model)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    async def execute(
        self,
        session_id: str,
        story_book: StoryBook,
        page_images: list[Image.Image],
        seed_images: Optional[dict[str, Image.Image]] = None
    ) -> Optional[str]:
        self.log_start("storage_operation", session_id=session_id)

        try:
            session_dir = self._create_session_directory(session_id)

            story_path = self._save_story_content(session_dir, story_book)
            images_saved = self._save_page_images(session_dir, page_images)
            seeds_saved = self._save_seed_images(session_dir, seed_images) if seed_images else True

            if story_path and images_saved and seeds_saved:
                self.log_success("storage_operation", session_id=session_id, story_path=str(story_path))
                return str(session_dir)
            else:
                self.log_failure("storage_operation", error="Failed to save all content", session_id=session_id)
                return None

        except Exception as e:
            self.log_failure("storage_operation", error=str(e), session_id=session_id)
            return None

    def _create_session_directory(self, session_id: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.storage_path / f"{session_id}_{timestamp}"
        session_dir.mkdir(exist_ok=True)

        (session_dir / "pages").mkdir(exist_ok=True)
        (session_dir / "seeds").mkdir(exist_ok=True)

        return session_dir

    def _save_story_content(self, session_dir: Path, story_book: StoryBook) -> Optional[Path]:
        try:
            story_path = session_dir / "story.json"

            story_dict = {
                "book_title": story_book.book_title,
                "pages": [
                    {
                        "title": page.title,
                        "text": page.text,
                        "scene_description": page.scene_description
                    }
                    for page in story_book.pages
                ]
            }

            with open(story_path, 'w', encoding='utf-8') as f:
                json.dump(story_dict, f, indent=2, ensure_ascii=False)

            return story_path

        except Exception:
            return None

    def _save_page_images(self, session_dir: Path, page_images: list[Image.Image]) -> bool:
        try:
            pages_dir = session_dir / "pages"

            for i, image in enumerate(page_images):
                image_path = pages_dir / f"page_{i+1:02d}.png"
                image.save(image_path, "PNG")

            return True

        except Exception:
            return False

    def _save_seed_images(self, session_dir: Path, seed_images: dict[str, Image.Image]) -> bool:
        try:
            seeds_dir = session_dir / "seeds"

            for entity_name, image in seed_images.items():
                safe_name = "".join(c for c in entity_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                image_path = seeds_dir / f"seed_{safe_name}.png"
                image.save(image_path, "PNG")

            return True

        except Exception:
            return False