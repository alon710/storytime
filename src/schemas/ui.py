from typing import Literal, Optional
from enum import Enum
from pydantic import BaseModel, Field

MessageRole = Literal["user", "assistant"]
MessageStatus = Literal["success", "error"]


class Status(str, Enum):
    """Status of a response or operation.

    Used for indicating success or error state in chat responses
    and other operations throughout the application.
    """
    SUCCESS = "success"
    ERROR = "error"


class ChatMessage(BaseModel):
    """Data model for a single chat message in the UI.

    Represents a message from either the user or assistant in the chat interface,
    including optional status and images.
    """

    role: MessageRole = Field(
        ...,
        description="The role of the message sender",
        examples=["user", "assistant"],
    )
    content: str = Field(
        ...,
        description="The text content of the message",
        min_length=1,
        examples=[
            "Hello, I need help creating a book for my child.",
            "I'd be happy to help! Tell me about your child.",
        ],
    )
    status: Optional[MessageStatus] = Field(
        None,
        description="Status of the message (only used for assistant messages)",
        examples=["success", "error"],
    )
    images: Optional[list[str]] = Field(
        None,
        description="List of image paths associated with this message",
        examples=[["/tmp/seed_image_abc123.png", "/tmp/page_1_illustration_xyz456.png"]],
    )
