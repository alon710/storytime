from enum import Enum

from typing import Annotated
from pydantic import Field
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.schemas.challenge import ChallengeData
from src.schemas.seed_image import SeedImageData


class Step(Enum):
    CHALLENGE_DISCOVERY = "challenge_discovery"
    SEED_IMAGE_GENERATION = "seed_image_generation"
    COMPLETE = "complete"


class State(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    challenge: ChallengeData
    seed_image: SeedImageData
    current_step: Step = Field(default=Step.CHALLENGE_DISCOVERY)
