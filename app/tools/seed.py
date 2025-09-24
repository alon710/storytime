from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image
else:
    try:
        from PIL import Image
    except ImportError:
        Image = None
from app.tools.base import BaseTool, BaseToolResponse
from typing import Type
from pydantic import Field


class SeedToolResponse(BaseToolResponse):
    seed_image_path: str | None = Field(None, description="Path to the generated seed image")
    requires_approval: bool = Field(True, description="Whether the seed image requires parent approval")
    child_name: str | None = Field(None, description="Name of the child")


class SeedTool(BaseTool):
    name: str = "use_reference_as_seed"
    description: str = (
        "Uses uploaded reference images as seed images for story character consistency"
    )

    def __init__(self, model: str):
        super().__init__(
            model=model,
            name="use_reference_as_seed",
            description="Uses uploaded reference images as seed images for story character consistency",
            system_prompt="Uses the uploaded reference photo of the child as the seed image for story consistency.",
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

            # Extract session_id from input context if not in args
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

            result = await self.execute(
                entity_type, entity_description, reference_images
            )

            # Save seed image and update session if successful
            if result and session_id:
                import os
                import tempfile

                # Save seed image temporarily
                temp_dir = tempfile.mkdtemp()
                seed_path = os.path.join(
                    temp_dir, f"seed_{entity_type}_{session_id}.png"
                )
                result.save(seed_path)

                # Update session with seed image
                session_manager = SessionManager()
                await session_manager.store_seed_image(session_id, seed_path)

                # Return structured response
                response = SeedToolResponse(
                    success=True,
                    message=f"Using your photo of {child_name} as the seed image. Please review and approve before proceeding with the story.",
                    seed_image_path=seed_path,
                    requires_approval=True,
                    child_name=child_name
                )
                return response.model_dump_json()

            # Return failure response
            response = SeedToolResponse(
                success=False,
                message=f"Failed to process seed image for {entity_type}",
                seed_image_path=None,
                requires_approval=False,
                child_name=child_name if 'child_name' in locals() else entity_type
            )
            return response.model_dump_json()
        except Exception as e:
            # Return structured error response
            response = SeedToolResponse(
                success=False,
                message=f"Error processing seed image: {str(e)}",
                seed_image_path=None,
                requires_approval=False,
                child_name=None
            )
            return response.model_dump_json()

    async def execute(
        self,
        entity_type: str,
        entity_description: str,
        reference_images: list[Image.Image] | None = None,
    ) -> Image.Image | None:
        self.log_start("seed_generation", entity_type=entity_type)

        try:
            # Simply use the first reference image as the seed
            if reference_images and len(reference_images) > 0:
                seed_image = reference_images[0]
                self.log_success(
                    "seed_generation",
                    entity_type=entity_type,
                    message="Using reference image as seed",
                )
                return seed_image
            else:
                self.log_failure(
                    "seed_generation",
                    error="No reference images provided",
                    entity_type=entity_type,
                )
                return None

        except Exception as e:
            self.log_failure("seed_generation", error=str(e), entity_type=entity_type)
            return None
