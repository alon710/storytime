from app.tools.base import BaseTool, BaseToolResponse
from typing import Type
from pydantic import Field
from PIL import Image
from app.settings import settings


class SeedToolResponse(BaseToolResponse):
    seed_image_path: str | None = Field(
        None, description="Path to the generated seed image"
    )
    requires_approval: bool = Field(
        True, description="Whether the seed image requires parent approval"
    )
    child_name: str | None = Field(None, description="Name of the child")


class SeedTool(BaseTool):
    model: str = settings.seed_model
    name: str = "use_reference_as_seed"
    description: str = (
        "Uses uploaded reference images as seed images for story character consistency"
    )

    def __init__(self):
        super().__init__(
            model=self.model,
            name="use_reference_as_seed",
            description="Uses uploaded reference images as seed images for story character consistency",
            system_prompt="You are an expert AI artist specializing in children's book characters. Your task is to generate a single image of a child with two distinct poses: a front-facing view on the left and a side profile view on the right. The final image should be suitable for use as a foundational \"seed image\" for future illustrations. The image must be a cohesive illustration. Maintain a consistent art style, lighting, and proportionality across both poses. The child's facial features, hairstyle, and clothing must be faithfully preserved based on the provided reference image. The background should be plain to maintain focus on the character. In a retro mid-century children’s book illustration style, in the spirit of Mary Blair and classic 1950s picture books. The image should faithfully preserve the child’s facial features, hairstyle, clothing, and proportions from the reference photo, ensuring consistency across poses. Stylized flat shapes, bold geometric forms, painterly textures, and a pastel-rich vintage color palette give the illustration a nostalgic feel. Plain, simple background for clarity.",
        )

    @property
    def response_model(self) -> Type[SeedToolResponse]:
        return SeedToolResponse

    async def _arun(self, **kwargs) -> str:
        try:
            # Handle different argument formats that LangChain might send
            if "args" in kwargs and isinstance(kwargs["args"], list) and kwargs["args"]:
                # LangChain passed args as a list
                args = kwargs["args"][0] if kwargs["args"] else {}
                child_name = args.get("child_name", args.get("name", "child"))
                age = args.get("age", 4)
                gender = args.get("gender", "child")
                entity_type = child_name
                entity_description = f"{age}-year-old {gender} named {child_name}"
                session_id = args.get("session_id")
                self.logger.info(
                    "Parsed tool arguments",
                    args=args,
                    session_id=session_id,
                    child_name=child_name,
                )
            else:
                # Direct keyword arguments
                entity_type = kwargs.get("entity_type", "child")
                entity_description = kwargs.get(
                    "entity_description", "A friendly child character"
                )
                session_id = kwargs.get("session_id")
                self.logger.info(
                    "Using direct kwargs", kwargs=kwargs, session_id=session_id
                )

            # Extract session_id from input context or kwargs
            if not session_id:
                # First try direct session_id in kwargs
                session_id = kwargs.get("session_id")

                # If not found, try extracting from input text
                if not session_id and "input" in kwargs:
                    input_text = kwargs.get("input", "")
                    if "Session ID:" in input_text:
                        import re

                        session_match = re.search(
                            r"Session ID:\s*([a-f0-9\-]+)", input_text
                        )
                        if session_match:
                            session_id = session_match.group(1)
                            self.logger.info(
                                "Extracted session_id from input", session_id=session_id
                            )

                # If still not found, check if it's embedded in the agent's full context
                if not session_id:
                    # LangChain might pass the entire agent input as a single string
                    all_input = str(kwargs)
                    if "Session ID:" in all_input:
                        import re

                        session_match = re.search(
                            r"Session ID:\s*([a-f0-9\-]+)", all_input
                        )
                        if session_match:
                            session_id = session_match.group(1)
                            self.logger.info(
                                "Extracted session_id from kwargs",
                                session_id=session_id,
                            )

            # Try to get reference images if session_id is available
            reference_images = None
            if session_id:
                from app.database.session_manager import SessionManager

                session_manager = SessionManager()
                reference_images = await session_manager.get_reference_images(
                    session_id
                )
                self.logger.info(
                    "Retrieved reference images",
                    session_id=session_id,
                    count=len(reference_images) if reference_images else 0,
                )

            # Pass child details to execute method
            result = await self.execute(
                entity_type,
                entity_description,
                reference_images,
                child_name if "child_name" in locals() else entity_type,
                age if "age" in locals() else 4,
                gender if "gender" in locals() else "child",
            )

            # Save seed image and update session if successful
            if result and session_id:
                from pathlib import Path

                # Create sessions directory in project root
                project_root = Path(__file__).parent.parent.parent
                sessions_dir = project_root / "sessions"
                session_dir = sessions_dir / session_id
                seeds_dir = session_dir / "seeds"

                # Create directories if they don't exist
                seeds_dir.mkdir(parents=True, exist_ok=True)

                # Save seed image to project directory
                seed_path = seeds_dir / f"seed_{entity_type}.png"
                result.save(seed_path)

                # Update session with seed image
                session_manager = SessionManager()
                await session_manager.store_seed_image(session_id, str(seed_path))

                # Return structured response
                response = SeedToolResponse(
                    success=True,
                    message=f"Using your photo of {child_name} as the seed image. Please review and approve before proceeding with the story.",
                    seed_image_path=str(seed_path),
                    requires_approval=True,
                    child_name=child_name,
                )
                return response.model_dump_json()

            # Return failure response
            response = SeedToolResponse(
                success=False,
                message=f"Failed to process seed image for {entity_type}",
                seed_image_path=None,
                requires_approval=False,
                child_name=child_name if "child_name" in locals() else entity_type,
            )
            return response.model_dump_json()
        except Exception as e:
            # Return structured error response
            response = SeedToolResponse(
                success=False,
                message=f"Error processing seed image: {str(e)}",
                seed_image_path=None,
                requires_approval=False,
                child_name=None,
            )
            return response.model_dump_json()

    async def execute(
        self,
        entity_type: str,
        entity_description: str,
        reference_images: list[Image.Image] | None = None,
        child_name: str = "child",
        age: int = 4,
        gender: str = "child",
    ) -> Image.Image | None:
        self.log_start("seed_generation", entity_type=entity_type)

        try:
            if not reference_images or len(reference_images) == 0:
                self.log_failure(
                    "seed_generation",
                    error="No reference images provided",
                    entity_type=entity_type,
                )
                return None

            # Use Gemini to generate a two-pose seed image based on the reference
            import google.genai as genai
            import asyncio
            from app.settings import settings

            client = genai.Client(api_key=settings.google_api_key)

            # Build the generation prompt combining system prompt with child details
            generation_prompt = f"""
{self.system_prompt}

Child details:
- Name: {child_name}
- Age: {age} years old
- Gender: {gender}
- Type: {entity_type}
- Description: {entity_description}

Please generate a seed image showing {child_name} (age {age}) in two poses side by side:
- Left side: front-facing view
- Right side: side profile view

IMPORTANT: The child should appear to be {age} years old based on their facial features, body proportions, and overall appearance. Use the reference image provided to maintain accurate facial features, hair, and appearance while ensuring the age representation is correct for a {age}-year-old {gender}.

The background should be plain and the art style should be consistent between both poses.
"""

            # Generate image using Gemini with reference image
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.model, contents=[generation_prompt] + reference_images
                ),
            )

            # Extract the generated image from response
            generated_image = self._extract_image_from_response(response)

            if generated_image:
                self.log_success(
                    "seed_generation",
                    entity_type=entity_type,
                    message="Successfully generated AI seed image with two poses",
                )
                return generated_image
            else:
                self.log_failure(
                    "seed_generation",
                    error="No image generated by AI model",
                    entity_type=entity_type,
                )
                return None

        except Exception as e:
            self.log_failure("seed_generation", error=str(e), entity_type=entity_type)
            return None

    def _extract_image_from_response(self, response) -> Image.Image | None:
        try:
            self.logger.info(
                "Extracting image from Gemini response",
                response_type=type(response).__name__,
            )

            # Try different ways to extract image from Gemini response
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(
                    candidate.content, "parts"
                ):
                    for part in candidate.content.parts:
                        if hasattr(part, "inline_data") and hasattr(
                            part.inline_data, "data"
                        ):
                            # Gemini inline_data.data contains raw image bytes, not base64
                            from io import BytesIO

                            image_data = part.inline_data.data
                            image = Image.open(BytesIO(image_data))
                            self.logger.info("Successfully extracted generated image")
                            return image

            # Log available attributes for debugging
            self.logger.warning(
                "Could not extract image", available_attrs=dir(response)
            )
            return None
        except Exception as e:
            self.logger.error("Error extracting image", error=str(e))
            return None
