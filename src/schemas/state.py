from typing import Literal, Union, Optional
from pydantic import BaseModel
from src.schemas.approval import NeedsApproval, Finalized


Role = Literal["user", "assistant"]
TurnResult = Union[NeedsApproval, Finalized]


class Message(BaseModel):
    role: Role
    text: str
    image_path: Optional[str] = None


class ChatState(BaseModel):
    messages: list[Message] = []