import uuid
from typing import Optional
from PIL import Image
from pydantic import BaseModel
import structlog

from .settings import settings
from .tools.seed import SeedTool
from .tools.narrator import NarratorTool
from .tools.illustrator import IllustratorTool
from .tools.storage import StorageTool

logger = structlog.get_logger()

TOOLS = {
    "seed": SeedTool(settings.seed_model),
    "narrator": NarratorTool(settings.narrator_model),
    "illustrator": IllustratorTool(settings.illustrator_model),
    "storage": StorageTool(settings.storage_backend, settings.session_storage_path),
}


class ChildMetaData(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    challenge: str | None = None
    reference_images: list[Image.Image] = []


class StoryTimeAgent:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.logger = logger.bind(session_id=self.session_id)
        self.tools = TOOLS
        self.child_metadata = ChildMetaData()

    async def create_story(
        self,
        child_metadata: ChildMetaData,
    ) -> Optional[str]:
        self.logger.info("Starting story creation workflow")

        try:
            seed_images = await self._generate_seed_images()
            if not seed_images:
                self.logger.error("Failed to generate seed images")
                return None

            story_book = await self._generate_story()
            if not story_book:
                self.logger.error("Failed to generate story")
                return None

            page_images = await self._generate_illustrations(story_book, seed_images)
            if not page_images:
                self.logger.error("Failed to generate illustrations")
                return None

            session_path = await self._save_session(
                story_book, page_images, seed_images
            )
            if session_path:
                self.logger.info(
                    "Story creation completed successfully", session_path=session_path
                )
                return session_path
            else:
                self.logger.error("Failed to save session")
                return None

        except Exception as e:
            self.logger.error("Story creation workflow failed", error=str(e))
            return None

    async def _generate_seed_images(self) -> Optional[dict[str, Image.Image]]:
        self.logger.info("Generating seed images")

        seed_images = {}

        child_description = (
            f"{self.child_age}-year-old {self.child_gender} named {self.child_name}"
        )
        child_seed = await self.seed_tool.execute(
            "child", child_description, self.reference_images
        )

        if child_seed:
            seed_images["child"] = child_seed
        else:
            return None

        return seed_images

    async def _generate_story(self):
        self.logger.info("Generating story content")

        return await self.narrator_tool.execute(
            self.child_name, self.child_age, self.child_gender, self.challenge_theme
        )

    async def _generate_illustrations(
        self, story_book, seed_images
    ) -> Optional[list[Image.Image]]:
        self.logger.info("Generating page illustrations")

        page_images = []
        previous_images = []

        for page in story_book.pages:
            illustration = await self.illustrator_tool.execute(
                page,
                seed_images,
                previous_images if len(previous_images) < 3 else previous_images[-3:],
            )

            if illustration:
                page_images.append(illustration)
                previous_images.append(illustration)
            else:
                self.logger.error(
                    "Failed to generate illustration for page", page_title=page.title
                )
                return None

        return page_images

    async def _save_session(
        self, story_book, page_images, seed_images
    ) -> Optional[str]:
        self.logger.info("Saving session content")

        return await self.storage_tool.execute(
            self.session_id, story_book, page_images, seed_images
        )
