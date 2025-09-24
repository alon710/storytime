from PIL import Image
import google.genai as genai
import asyncio
from app.tools.base import BaseTool, BaseToolResponse
from app.tools.narrator import StoryPage
from typing import Type
from pydantic import Field
from app.settings import settings


class IllustratorToolResponse(BaseToolResponse):
    illustration_path: str | None = Field(
        None, description="Path to the generated illustration"
    )
    page_title: str | None = Field(None, description="Title of the illustrated page")


class IllustratorTool(BaseTool):
    name: str = "generate_illustration"
    description: str = "Creates children's book page illustrations using story content, seed images, and previous pages for visual consistency"
    system_prompt: str = """You are an AI illustrator specializing in children's book artwork.
Your role is to create beautiful, consistent illustrations that bring stories to life.
Maintain character consistency using seed images and ensure visual continuity across pages."""

    def __init__(self):
        super().__init__(
            model=settings.illustrator_model,
            name="generate_illustration",
            description="Creates children's book page illustrations using story content, seed images, and previous pages for visual consistency",
            system_prompt="""You are an AI illustrator specializing in children's book artwork.
Your role is to create beautiful, consistent illustrations that bring stories to life.
Maintain character consistency using seed images and ensure visual continuity across pages.""",
        )

    @property
    def response_model(self) -> Type[IllustratorToolResponse]:
        return IllustratorToolResponse

    async def _arun(self, **kwargs) -> str:
        try:
            # Handle different argument formats that LangChain might send
            if "args" in kwargs and isinstance(kwargs["args"], list) and kwargs["args"]:
                kwargs["args"][0] if kwargs["args"] else {}
                # For now, create a simple placeholder story page
                from app.tools.narrator import StoryPage

                story_page = StoryPage(
                    title="Sample Page",
                    text="This is a sample story page.",
                    scene_description="A cheerful scene with the main character.",
                )
            else:
                # Try to extract story page from kwargs
                from app.tools.narrator import StoryPage
                import json

                if "story_page" in kwargs:
                    page_data = json.loads(kwargs["story_page"])
                    story_page = StoryPage(**page_data)
                else:
                    story_page = StoryPage(
                        title="Sample Page",
                        text="This is a sample story page.",
                        scene_description="A cheerful scene with the main character.",
                    )

            result = await self.execute(story_page, {}, [])
            return (
                "Generated page illustration"
                if result
                else "Failed to generate illustration"
            )
        except Exception as e:
            return f"Error generating illustration: {str(e)}"

    async def execute(
        self,
        story_page: StoryPage,
        seed_images: dict[str, Image.Image],
        previous_page_images: list[Image.Image] | None = None,
    ) -> Image.Image | None:
        self.log_start("illustration_generation", page_title=story_page.title)

        try:
            prompt = self._build_illustration_prompt(story_page)

            from app.settings import settings

            client = genai.Client(api_key=settings.google_api_key)

            contents = [prompt]

            if seed_images:
                for entity, seed_image in seed_images.items():
                    contents.extend([f"Seed image for {entity}:", seed_image])

            if previous_page_images:
                contents.extend(
                    ["Previous page illustrations for consistency:"]
                    + previous_page_images
                )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.model, contents=contents
                ),
            )

            illustration = self._extract_image_from_response(response)

            if illustration:
                self.log_success("illustration_generation", page_title=story_page.title)
                return illustration
            else:
                self.log_failure(
                    "illustration_generation",
                    error="No illustration generated",
                    page_title=story_page.title,
                )
                return None

        except Exception as e:
            self.log_failure(
                "illustration_generation", error=str(e), page_title=story_page.title
            )
            return None

    def _build_illustration_prompt(self, story_page: StoryPage) -> str:
        return f"""Create a children's book illustration for this page:

Title: {story_page.title}
Text: {story_page.text}
Scene: {story_page.scene_description}

Style requirements:
- Warm, friendly children's book illustration style
- Consistent with provided seed images for characters
- Maintain visual continuity with previous pages
- Bright, engaging colors appropriate for ages 3-8
- Clear, simple composition that supports the story text
- High quality, professional children's book illustration

Please use the seed images to maintain character consistency and create a beautiful page illustration that matches the scene description."""

    def _extract_image_from_response(self, response) -> Image.Image | None:
        try:
            if hasattr(response, "image") and response.image:
                return response.image
            return None
        except Exception:
            return None
