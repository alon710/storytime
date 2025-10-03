from typing import Literal, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


from schemas.challenge import ChallengeData
from schemas.book import BookContent


WorkflowStep = Literal["discovery", "seed_image", "narration", "illustration", "pdf_generation", "completed"]


class WorkflowState(BaseModel):
    """Complete state of the book creation workflow for a session.

    Tracks which step the workflow is on, what data has been produced by each tool,
    what has been approved by the parent, and when state changes occurred.
    """

    current_step: WorkflowStep = Field(
        default="discovery",
        description="Current step in the workflow",
        examples=["discovery", "seed_image", "narration"],
    )
    challenge_data: Optional[ChallengeData] = Field(None, description="Challenge information from discovery phase")
    seed_image_path: Optional[Path] = Field(
        None, description="Path to the generated seed character image", examples=["/tmp/seed_image_abc123.png"]
    )
    book_content: Optional[BookContent] = Field(None, description="Complete book content from narrator")
    illustrations: Optional[dict[int, Path]] = Field(
        default_factory=dict,
        description="Map of page number to illustration path",
        examples=[{1: "/tmp/page_1_illustration.png", 2: "/tmp/page_2_illustration.png"}],
    )
    pdf_path: Optional[Path] = Field(
        None, description="Path to the final generated PDF", examples=["/tmp/book_emma_brave_night.pdf"]
    )
    approvals: dict[WorkflowStep, bool] = Field(
        default_factory=dict,
        description="Approval status for each workflow step",
        examples=[{"discovery": True, "seed_image": True}],
    )
    created_at: datetime = Field(default_factory=datetime.now, description="When this workflow state was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When this workflow state was last updated")

    @field_validator("seed_image_path", "pdf_path", mode="before")
    @classmethod
    def convert_str_to_path(cls, v):
        """Convert string paths to Path objects."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("illustrations", mode="before")
    @classmethod
    def convert_illustrations_paths(cls, v):
        """Convert illustration paths from strings to Path objects."""
        if v is None:
            return {}
        if isinstance(v, dict):
            return {int(k): Path(p) if isinstance(p, str) else p for k, p in v.items()}
        return v

    def is_step_completed(self, step: WorkflowStep) -> bool:
        """Check if a specific workflow step has been completed.

        A step is considered completed if it has produced the expected data.
        """
        if step == "discovery":
            return self.challenge_data is not None
        elif step == "seed_image":
            return self.seed_image_path is not None
        elif step == "narration":
            return self.book_content is not None
        elif step == "illustration":
            if self.book_content is None:
                return False
            expected_pages = self.book_content.total_pages
            return len(self.illustrations) == expected_pages
        elif step == "pdf_generation":
            return self.pdf_path is not None
        elif step == "completed":
            return True
        return False

    def is_step_approved(self, step: WorkflowStep) -> bool:
        """Check if a specific workflow step has been approved by the parent."""
        return self.approvals.get(step, False)

    def can_proceed_to_next_step(self) -> bool:
        """Check if the workflow can proceed to the next step.

        Requires both completion and approval of the current step.
        """
        return self.is_step_completed(self.current_step) and self.is_step_approved(self.current_step)

    def get_next_step(self) -> Optional[WorkflowStep]:
        """Get the next workflow step based on current step."""
        step_order: list[WorkflowStep] = [
            "discovery",
            "seed_image",
            "narration",
            "illustration",
            "pdf_generation",
            "completed",
        ]
        try:
            current_index = step_order.index(self.current_step)
            if current_index < len(step_order) - 1:
                return step_order[current_index + 1]
        except ValueError:
            pass
        return None

