"""Centralized schemas module for the application.

This module provides domain-separated Pydantic v2 BaseModels for data validation
and type safety across the application.
"""

from schemas.challenge import ChallengeData
from schemas.book import BookPage, BookContent
from schemas.workflow import WorkflowStep, WorkflowState
from schemas.common import ToolResponse
from schemas.ui import MessageRole, MessageStatus, ChatMessage, Status

__all__ = [
    # Challenge schemas
    "ChallengeData",
    # Book schemas
    "BookPage",
    "BookContent",
    # Workflow schemas
    "WorkflowStep",
    "WorkflowState",
    # Common schemas
    "ToolResponse",
    # UI schemas
    "MessageRole",
    "MessageStatus",
    "ChatMessage",
    "Status",
]
