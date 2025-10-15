from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.schemas.challenge import ChallengeData
from src.schemas.seed_image import SeedImageData
from src.schemas.book import BookData
from langgraph.graph import END
from enum import Enum


class NextAction(str, Enum):
    CONTINUE = "continue"
    RETRY = "retry"
    END = END


class State(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    challenge: ChallengeData
    seed_image: SeedImageData
    book: BookData
    next_action: NextAction
