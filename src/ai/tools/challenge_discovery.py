from langchain_core.tools import tool
from typing import Optional
from core.settings import settings
from core.session import session_context
from core.workflow_state import workflow_state_manager
from core.logger import logger
from schemas.challenge import ChallengeData
from schemas.common import ToolResponse


def _infer_challenge_type(challenge_description: str) -> str:
    """Infer challenge type from description using simple keyword matching.

    Args:
        challenge_description: The detailed challenge description from parent

    Returns:
        A categorized challenge type string
    """
    description_lower = challenge_description.lower()

    # Common challenge patterns
    if any(word in description_lower for word in ["dark", "darkness", "night", "afraid of dark"]):
        return "fear of dark"
    elif any(word in description_lower for word in ["school", "kindergarten", "classroom", "teacher"]):
        return "starting school"
    elif any(word in description_lower for word in ["sibling", "baby", "brother", "sister", "new baby"]):
        return "new sibling"
    elif any(word in description_lower for word in ["move", "moving", "new house", "new home"]):
        return "moving to new house"
    elif any(word in description_lower for word in ["friend", "friendship", "making friends", "shy"]):
        return "making friends"
    elif any(word in description_lower for word in ["separation", "leaving", "parent leaving", "daycare"]):
        return "separation anxiety"
    elif any(word in description_lower for word in ["monster", "scary", "nightmare", "afraid"]):
        return "fear and anxiety"
    elif any(word in description_lower for word in ["share", "sharing", "toy", "selfish"]):
        return "learning to share"
    elif any(word in description_lower for word in ["potty", "toilet", "bathroom", "diaper"]):
        return "potty training"
    elif any(word in description_lower for word in ["angry", "tantrum", "emotions", "feelings"]):
        return "managing emotions"
    else:
        # Generic fallback - extract first few words
        words = challenge_description.split()
        return " ".join(words[:4]) if len(words) >= 4 else challenge_description


@tool(description=settings.tools.challenge_discovery.tool_description)
def discover_challenge(
    child_name: str,
    child_age: int,
    challenge_description: str,
    desired_outcome: str,
    child_gender: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> dict:
    """Discover and structure the child's challenge information.

    This tool validates and structures the information gathered from the parent
    about their child's challenge. It's the first step in creating a personalized
    children's book.

    Args:
        child_name: The child's name
        child_age: The child's age in years (1-18)
        challenge_description: Detailed description of the challenge
        desired_outcome: What the parent hopes the child will learn or feel
        child_gender: Optional gender of the child
        additional_context: Any additional context or special requests

    Returns:
        dict: Serialized ToolResponse[ChallengeData] with success status and data
    """
    session_id = session_context.get_current_session()

    logger.info(
        "Challenge discovery started",
        session_id=session_id,
        child_name=child_name,
        child_age=child_age,
    )

    try:
        # Validate age
        if not (1 <= child_age <= 18):
            error_msg = f"Invalid age: {child_age}. Age must be between 1 and 18."
            logger.error("Challenge discovery validation failed", error=error_msg, session_id=session_id)
            return ToolResponse[ChallengeData](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        # Validate required fields
        if not child_name.strip():
            error_msg = "Child name cannot be empty"
            logger.error("Challenge discovery validation failed", error=error_msg, session_id=session_id)
            return ToolResponse[ChallengeData](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        if not challenge_description.strip():
            error_msg = "Challenge description cannot be empty"
            logger.error("Challenge discovery validation failed", error=error_msg, session_id=session_id)
            return ToolResponse[ChallengeData](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        if not desired_outcome.strip():
            error_msg = "Desired outcome cannot be empty"
            logger.error("Challenge discovery validation failed", error=error_msg, session_id=session_id)
            return ToolResponse[ChallengeData](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        # Infer challenge type from description
        challenge_type = _infer_challenge_type(challenge_description)
        logger.info("Inferred challenge type", challenge_type=challenge_type, session_id=session_id)

        # Create ChallengeData instance
        challenge_data = ChallengeData(
            challenge_type=challenge_type,
            details=challenge_description.strip(),
            child_name=child_name.strip(),
            child_age=child_age,
            child_gender=child_gender.strip() if child_gender else None,
            desired_outcome=desired_outcome.strip(),
            additional_context=additional_context.strip() if additional_context else None,
        )

        logger.info(
            "Challenge data created successfully",
            session_id=session_id,
            challenge_type=challenge_data.challenge_type,
            child_name=challenge_data.child_name,
        )

        # Update workflow state
        if session_id:
            workflow_state_manager.update_workflow_state(
                session_id=session_id,
                challenge_data=challenge_data,
            )
            logger.info("Workflow state updated with challenge data", session_id=session_id)
        else:
            logger.warning("No session_id available, skipping workflow state update")

        # Return success response
        response = ToolResponse[ChallengeData](
            success=True,
            data=challenge_data,
            error_message=None,
            metadata={
                "session_id": session_id,
                "challenge_type": challenge_data.challenge_type,
                "step_completed": "discovery",
            },
        )

        logger.info("Challenge discovery completed successfully", session_id=session_id)
        return response.model_dump()

    except Exception as e:
        error_msg = f"Challenge discovery failed: {str(e)}"
        logger.error(
            "Challenge discovery error",
            error=str(e),
            error_type=type(e).__name__,
            session_id=session_id,
        )
        return ToolResponse[ChallengeData](
            success=False,
            data=None,
            error_message=error_msg,
            metadata={"session_id": session_id, "error_type": type(e).__name__},
        ).model_dump()
