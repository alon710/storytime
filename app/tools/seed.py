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

    async def _arun(self, **kwargs) -> str:
        try:
            # Handle different argument formats that LangChain might send
            if "args" in kwargs and isinstance(kwargs["args"], list) and kwargs["args"]:
                # LangChain passed args as a list
                args = kwargs["args"][0] if kwargs["args"] else {}
                entity_type = args.get("name", "child")
                entity_description = f"{args.get('age', 4)}-year-old {args.get('gender', 'child')} named {args.get('name', 'child')}"
                session_id = args.get("session_id")
            else:
                # Direct keyword arguments
                entity_type = kwargs.get("entity_type", "child")
                entity_description = kwargs.get("entity_description", "A friendly child character")
                session_id = kwargs.get("session_id")

            # Try to get reference images if session_id is available
            reference_images = None
            if session_id:
                from app.database.session_manager import SessionManager
                session_manager = SessionManager()
                reference_images = await session_manager.get_reference_images(session_id)

            result = await self.execute(entity_type, entity_description, reference_images)

            # Save seed image and update session if successful
            if result and session_id:
                import os
                import tempfile

                # Save seed image temporarily
                temp_dir = tempfile.mkdtemp()
                seed_path = os.path.join(temp_dir, f"seed_{entity_type}_{session_id}.png")
                result.save(seed_path)

                # Update session with seed image
                session_manager = SessionManager()
                await session_manager.store_seed_image(session_id, seed_path)

                return f"Generated seed image for {entity_type}. Please review and approve before proceeding with the story."

            return f"Generated seed image for {entity_type}" if result else f"Failed to generate seed image for {entity_type}"
        except Exception as e:
            return f"Error generating seed image: {str(e)}"
    async def execute(
        self,
        entity_type: str,
        entity_description: str,
        reference_images: list[Image.Image] | None = None
    ) -> Image.Image | None:
        self.log_start("seed_generation", entity_type=entity_type)

        try:
            prompt = self._build_seed_prompt(entity_type, entity_description)

            from app.settings import settings
            client = genai.Client(api_key=settings.google_api_key)

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