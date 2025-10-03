from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ToolResponse(BaseModel, Generic[T]):
    """Generic response model for all tool operations.

    Provides a consistent interface for tool results with success/error handling.
    """

    success: bool = Field(..., description="Whether the tool operation succeeded")
    data: Optional[T] = Field(None, description="The tool's output data if successful")
    error_message: Optional[str] = Field(None, description="Error message if operation failed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the operation")

    model_config = ConfigDict(arbitrary_types_allowed=True)
