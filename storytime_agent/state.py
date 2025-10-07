from typing import Annotated
from pydantic import Field
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from storytime_agent.schemas.state import Step, Gender


class State(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: Step = Field(default=Step.CHALLENGE_DISCOVERY)
    child_name: str
    child_age: int
    child_gender: Gender
    challenge_description: str
    additional_context: str


__all__ = ["State"]
