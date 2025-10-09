from enum import Enum
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from src.config import settings


class ApprovalIntent(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    UNCLEAR = "unclear"


class ApprovalClassification(BaseModel):
    intent: ApprovalIntent
    reasoning: str


def filter_image_content(messages: list) -> list:
    """Filter out image content from messages, keeping only text"""
    filtered = []
    for msg in messages:
        if isinstance(msg, HumanMessage) and isinstance(msg.content, list):
            text_content = [item for item in msg.content if item.get("type") == "text"]
            if text_content:
                filtered.append(HumanMessage(content=text_content))
        else:
            filtered.append(msg)
    return filtered


def get_approval_llm(name: str) -> ChatGoogleGenerativeAI:
    """Create a standardized LLM for approval classification and responses"""
    return ChatGoogleGenerativeAI(
        google_api_key=settings.google_api_key,
        model=settings.seed_image.model,
        temperature=settings.seed_image.temperature,
        max_output_tokens=settings.seed_image.max_tokens,
        name=name,
    )


def classify_approval_intent(user_message: str, context: str, llm: ChatGoogleGenerativeAI) -> ApprovalClassification:
    prompt = f"""Analyze the user's message to determine if they are approving, rejecting, or being unclear about {context}.

User message: "{user_message}"

Classify the user's intent as one of:
- APPROVE: User explicitly approves and wants to proceed to the next step. They are satisfied and ready to continue.
- REJECT: User wants changes, corrections, or to start over. They mentioned specific things to change or expressed dissatisfaction.
- UNCLEAR: User is asking questions, requesting more information, or their intent is ambiguous. They haven't given a clear yes/no.

Important:
- If user says something is good BUT mentions ANY changes they want, classify as REJECT
- If user asks clarifying questions, classify as UNCLEAR
- Only classify as APPROVE if user clearly wants to proceed without changes

Return your classification with brief reasoning."""

    try:
        result = llm.with_structured_output(ApprovalClassification).invoke([SystemMessage(content=prompt)])
        if isinstance(result, ApprovalClassification):
            return result
        return ApprovalClassification(
            intent=ApprovalIntent.UNCLEAR, reasoning="Invalid classification format"
        )
    except Exception:
        return ApprovalClassification(
            intent=ApprovalIntent.UNCLEAR, reasoning="Failed to classify intent, defaulting to unclear"
        )
