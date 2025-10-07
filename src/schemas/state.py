from enum import Enum

from typing import Annotated
from pydantic import Field
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class Step(Enum):
    CHALLENGE_DISCOVERY = "challenge_discovery"
    SEED_IMAGE_GENERATION = "seed_image_generation"
    COMPLETE = "complete"


class Gender(Enum):
    BOY = "boy"
    GIRL = "girl"


class State(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: Step = Field(default=Step.CHALLENGE_DISCOVERY)
    child_name: str
    child_age: int
    child_gender: Gender
    challenge_description: str
    additional_context: str


__all__ = ["State"]
