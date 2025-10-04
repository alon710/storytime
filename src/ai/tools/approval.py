from langchain_core.tools import tool
from typing import Literal

from core.session import session_context
from core.workflow_state import workflow_state_manager
from core.logger import logger
from schemas.workflow import WorkflowStep
from schemas.common import ToolResponse


# Create a Literal type for valid step names to help the agent
ApprovalStepName = Literal["discovery", "seed_image", "narration", "illustration", "pdf_generation"]


@tool(description="Mark a workflow step as approved by the parent. Use this when the parent explicitly approves generated content (seed image, book content, etc.) and wants to proceed to the next step.")
def approve_step(
    step_name: str,  # Must be string for LangChain compatibility, validated internally
) -> dict:
    """Approve a workflow step after parent review.

    This tool marks a completed workflow step as approved, allowing the workflow
    to proceed to the next step. Use this when the parent explicitly indicates
    approval of generated content (e.g., "yes", "looks good", "approve", "proceed").

    Args:
        step_name: Name of the step to approve. Must be one of:
                  - "discovery" (challenge discovery)
                  - "seed_image" (seed character image)
                  - "narration" (book content/story)
                  - "illustration" (page illustrations)
                  - "pdf_generation" (final PDF)

    Returns:
        dict: Serialized ToolResponse[str] indicating success or error
    """
    session_id = session_context.get_current_session() or "default"

    logger.info(
        "Approval requested",
        session_id=session_id,
        step_name=step_name,
    )

    try:
        # Validate step_name
        valid_steps = ["discovery", "seed_image", "narration", "illustration", "pdf_generation", "completed"]
        if step_name not in valid_steps:
            error_msg = f"Invalid step_name '{step_name}'. Must be one of: {', '.join(valid_steps)}"
            logger.error("Approval validation failed", error=error_msg, session_id=session_id)
            return ToolResponse[str](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id, "provided_step": step_name},
            ).model_dump()

        step: WorkflowStep = step_name  # type: ignore

        # Get current workflow state
        workflow_state = workflow_state_manager.get_workflow_state(session_id)

        # Check if step is actually completed
        if not workflow_state.is_step_completed(step):
            error_msg = (
                f"Cannot approve '{step_name}' - step is not yet completed. "
                f"Please complete the step first before requesting approval."
            )
            logger.error("Approval failed - step not completed", step=step_name, session_id=session_id)
            return ToolResponse[str](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id, "step": step_name, "is_completed": False},
            ).model_dump()

        # Check if already approved
        if workflow_state.is_step_approved(step):
            message = f"Step '{step_name}' is already approved."
            logger.info("Step already approved", step=step_name, session_id=session_id)
            return ToolResponse[str](
                success=True,
                data=message,
                error_message=None,
                metadata={"session_id": session_id, "step": step_name, "already_approved": True},
            ).model_dump()

        # Mark step as approved
        workflow_state_manager.mark_step_approved(session_id, step)

        success_message = (
            f"✓ Step '{step_name}' has been approved! "
            f"The parent has confirmed they're happy with the {step_name.replace('_', ' ')} and we can proceed."
        )

        logger.info("Step approved successfully", step=step_name, session_id=session_id)

        return ToolResponse[str](
            success=True,
            data=success_message,
            error_message=None,
            metadata={
                "session_id": session_id,
                "step": step_name,
                "approved": True,
                "can_proceed": workflow_state_manager.can_proceed_to_next_step(session_id),
            },
        ).model_dump()

    except Exception as e:
        error_msg = f"Failed to approve step: {str(e)}"
        logger.error(
            "Approval error",
            error=str(e),
            error_type=type(e).__name__,
            step_name=step_name,
            session_id=session_id,
        )
        return ToolResponse[str](
            success=False,
            data=None,
            error_message=error_msg,
            metadata={"session_id": session_id, "error_type": type(e).__name__},
        ).model_dump()
