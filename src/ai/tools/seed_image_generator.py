from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from pathlib import Path
from typing import Optional
import base64
import mimetypes

from core.settings import settings
from core.session import session_context
from core.workflow_state import workflow_state_manager
from core.logger import logger
from core.temp_files import temp_file_manager
from schemas.common import ToolResponse


@tool(
    description="Generate a seed character image from the child's photo to use as reference for all book illustrations. REQUIRES: discover_challenge must be completed first. Creates a hero-style character in children's book style suitable as a consistent reference throughout the story."
)
def generate_seed_image(
    child_image_path: str,  # LangChain tools work better with str, we convert to Path internally
    parent_description: Optional[str] = None,
) -> dict:
    """Generate seed character image for the children's book.

    Creates a hero-style character reference image from the child's photo that will
    be used as the basis for all subsequent illustrations in the book.

    IMPORTANT: This tool requires that discover_challenge has been completed first.
    It retrieves the challenge data from the workflow state automatically.

    Args:
        child_image_path: Path to the uploaded child photo
        parent_description: Optional additional styling requests from parent

    Returns:
        dict: Serialized ToolResponse[Path] with seed image path or error
    """
    session_id = session_context.get_current_session() or "default"
    child_path = Path(child_image_path)

    logger.info(
        "Seed image generation started",
        session_id=session_id,
        child_image_path=str(child_path),
        has_parent_description=bool(parent_description),
    )

    try:
        # Retrieve challenge data from workflow state
        workflow_state = workflow_state_manager.get_workflow_state(session_id)

        if not workflow_state.challenge_data:
            error_msg = "Challenge data not found in workflow state. Please complete discover_challenge first."
            logger.error("Seed image generation failed - missing challenge data", session_id=session_id)
            return ToolResponse[Path](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id, "required_step": "discover_challenge"},
            ).model_dump()

        challenge_data = workflow_state.challenge_data

        # Validate child image exists
        if not child_path.exists():
            error_msg = f"Child image not found: {child_path}"
            logger.error("Seed image generation failed", error=error_msg, session_id=session_id)
            return ToolResponse[Path](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        # Build prompt for seed image generation
        base_prompt = f"""Create a hero-style character illustration of {challenge_data.child_name}, a {challenge_data.child_age}-year-old child, based on the reference photo.

This is a seed character image for a children's book where {challenge_data.child_name} overcomes the challenge of: {challenge_data.challenge_type}.

REQUIREMENTS:
- Synthesize features from all reference images to create a consistent character design
- Both poses should be consistent - same clothing, hair, and features
- Clear split composition with both poses in the same image
- No text or labels in the image
- Child-friendly, warm, and welcoming style
- Both poses should be full body or at least torso up
- Maintain consistent proportions between both poses
- Apply the specified art style uniformly to both poses
- Clean white or simple background

COMPOSITION:
- Single cohesive image with two character poses
- Left pose: Front view facing forward
- Right pose: Side profile view
- Both poses should be clearly visible and well-proportioned
- Consistent lighting and art style across both poses

This image will be used as a reference for all subsequent book illustrations to maintain character consistency."""

        if parent_description:
            base_prompt += f"\n\nAdditional parent requests: {parent_description}"

        # Build message content with child image
        message_content = [{"type": "text", "text": base_prompt}]

        if child_path.exists():
            # Detect MIME type from file
            mime_type, _ = mimetypes.guess_type(str(child_path))
            if not mime_type or not mime_type.startswith("image/"):
                # Default to jpeg if detection fails or not an image
                mime_type = "image/jpeg"

            logger.info("Image MIME type detected", mime_type=mime_type, path=str(child_path), session_id=session_id)

            with open(child_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
                message_content.append(
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_data}"}}
                )

        # Generate seed image
        image_llm = ChatGoogleGenerativeAI(
            model=settings.tools.seed_image_generator.model_name,
            google_api_key=settings.tools.seed_image_generator.api_key.get_secret_value(),
            temperature=settings.tools.seed_image_generator.temperature,
            max_output_tokens=settings.tools.seed_image_generator.max_output_tokens,
        )

        message = HumanMessage(content=message_content)
        generation_config = {"response_modalities": ["TEXT", "IMAGE"]}
        response = image_llm.invoke(input=[message], generation_config=generation_config)

        # Extract first generated image
        seed_image_path = None
        if isinstance(response.content, list):
            for block in response.content:
                if isinstance(block, dict) and "image_url" in block:
                    image_data = block["image_url"]["url"].split(",")[-1]
                    temp_path_str = temp_file_manager.save_from_base64(image_data, prefix="seed_image_")
                    seed_image_path = Path(temp_path_str)
                    logger.info("Seed image generated and saved", path=str(seed_image_path), session_id=session_id)
                    break  # Only take the first image

        if not seed_image_path:
            error_msg = "No image was generated in the response"
            logger.error("Seed image generation failed", error=error_msg, session_id=session_id)
            return ToolResponse[Path](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        # Update workflow state
        if session_id:
            workflow_state_manager.update_workflow_state(
                session_id=session_id,
                seed_image_path=seed_image_path,
            )
            logger.info("Workflow state updated with seed image path", session_id=session_id, path=str(seed_image_path))

            # Add image to session artifacts so it displays to parent
            session_context.add_artifacts("images", str(seed_image_path), session_id)
            logger.info("Seed image added to session artifacts for display", session_id=session_id)
        else:
            logger.warning("No session_id available, skipping workflow state update")

        # Return success response
        response_data = ToolResponse[Path](
            success=True,
            data=seed_image_path,
            error_message=None,
            metadata={
                "session_id": session_id,
                "child_name": challenge_data.child_name,
                "challenge_type": challenge_data.challenge_type,
                "step_completed": "seed_image",
            },
        )

        logger.info("Seed image generation completed successfully", session_id=session_id)
        return response_data.model_dump()

    except Exception as e:
        error_msg = f"Seed image generation failed: {str(e)}"
        logger.error(
            "Seed image generation error",
            error=str(e),
            error_type=type(e).__name__,
            session_id=session_id,
        )
        return ToolResponse[Path](
            success=False,
            data=None,
            error_message=error_msg,
            metadata={"session_id": session_id, "error_type": type(e).__name__},
        ).model_dump()
