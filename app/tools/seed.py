from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image
else:
    try:
        from PIL import Image
    except ImportError:
        Image = None
import google.genai as genai
import asyncio
from app.tools.base import BaseTool


class SeedTool(BaseTool):
    name: str = "generate_seed_image"
    description: str = "Generates consistent character seed images for story illustrations based on entity descriptions and reference images"
    system_prompt: str = """You are an AI artist specializing in children's book character design.
Your role is to create seed images that establish consistent character appearances for storytelling.
Focus on warm, friendly designs suitable for ages 3-8 with clear, recognizable features that can be maintained across multiple story pages."""

    def __init__(self, model: str):
        super().__init__(
            model=model,
            name="generate_seed_image",
            description="Generates consistent character seed images for story illustrations based on entity descriptions and reference images",
            system_prompt="""You are an AI artist specializing in children's book character design.
Your role is to create seed images that establish consistent character appearances for storytelling.
Focus on warm, friendly designs suitable for ages 3-8 with clear, recognizable features that can be maintained across multiple story pages."""
        )

    async def _arun(self, entity_type: str, entity_description: str, reference_images: str | None = None) -> str:
        result = await self.execute(entity_type, entity_description, reference_images)
        return f"Generated seed image for {entity_type}" if result else f"Failed to generate seed image for {entity_type}"
    async def execute(
        self,
        entity_type: str,
        entity_description: str,
        reference_images: list[Image.Image] | None = None
    ) -> Image.Image | None:
        self.log_start("seed_generation", entity_type=entity_type)

        try:
            prompt = self._build_seed_prompt(entity_type, entity_description)

            client = genai.Client()

            loop = asyncio.get_event_loop()
            if reference_images:
                response = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=self.model,
                        contents=[prompt] + reference_images
                    )
                )
            else:
                response = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=self.model,
                        contents=prompt
                    )
                )

            seed_image = self._extract_image_from_response(response)

            if seed_image:
                self.log_success("seed_generation", entity_type=entity_type)
                return seed_image
            else:
                self.log_failure("seed_generation", error="No image generated", entity_type=entity_type)
                return None

        except Exception as e:
            self.log_failure("seed_generation", error=str(e), entity_type=entity_type)
            return None

    def _build_seed_prompt(self, entity_type: str, description: str) -> str:
        return f"""Generate a seed image for a children's book character.

Entity type: {entity_type}
Description: {description}

Style requirements:
- Warm, friendly children's book illustration style
- Consistent character design suitable for multiple scenes
- Clear, recognizable features that can be maintained across pages
- Appropriate for ages 3-8

Please create a high-quality character seed image."""

    def _extract_image_from_response(self, response) -> Image.Image | None:
        try:
            if hasattr(response, 'image') and response.image:
                return response.image
            return None
        except Exception:
            return None