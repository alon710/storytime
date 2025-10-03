from typing import Optional
from pydantic import BaseModel, Field


class ChallengeData(BaseModel):
    """Data model for the child's challenge that the book will address.

    Contains all information gathered during the discovery phase about the child
    and the specific challenge they're facing.
    """

    challenge_type: str = Field(
        ...,
        description='Type of challenge (e.g., "fear of dark", "starting school", "new sibling")',
        min_length=1,
        examples=["fear of dark", "starting school", "new sibling", "moving to a new house"],
    )
    details: str = Field(
        ...,
        description="Detailed description of the challenge from the parent",
        min_length=1,
        examples=["My daughter gets very anxious at bedtime and refuses to sleep with the lights off."],
    )
    child_name: str = Field(..., description="The child's name", min_length=1, examples=["Emma", "Jack", "Sofia"])
    child_age: int = Field(..., description="The child's age in years", ge=1, le=18, examples=[5, 6, 7])
    child_gender: Optional[str] = Field(
        None, description="The child's gender (if provided)", examples=["female", "male", "non-binary"]
    )
    desired_outcome: str = Field(
        ...,
        description="What the parent hopes the child will learn or feel from the book",
        min_length=1,
        examples=["I want her to feel brave and understand that darkness is nothing to fear."],
    )
    additional_context: Optional[str] = Field(
        None,
        description="Any additional context or specific requests from the parent",
        examples=["She loves stories about brave princesses and magical creatures."],
    )

