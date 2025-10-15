from pathlib import Path
from typing import TypeVar, Type
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.base import BaseMessage
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_prompt(prompt_name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.txt"

    if not prompt_path.exists():
        raise FileNotFoundError("Prompt file not found")

    return prompt_path.read_text(encoding="utf-8").strip()


def filter_image_content(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Filter out image content from messages, keeping only text"""
    from langchain_core.messages import SystemMessage

    filtered = []
    for msg in messages:
        content = msg.content if hasattr(msg, "content") else msg.get("content") if isinstance(msg, dict) else None

        if isinstance(content, list):
            text_content = [item for item in content if isinstance(item, dict) and item.get("type") == "text"]
            if text_content:
                if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get("type") == "human"):
                    filtered.append(HumanMessage(content=text_content))
                elif isinstance(msg, AIMessage) or (isinstance(msg, dict) and msg.get("type") == "ai"):
                    filtered.append(AIMessage(content=text_content))
                elif isinstance(msg, SystemMessage) or (isinstance(msg, dict) and msg.get("type") == "system"):
                    filtered.append(SystemMessage(content=text_content))

        else:
            filtered.append(msg)
    return filtered


def extract_image_urls(messages: list) -> list[str]:
    image_urls = []
    for message in messages:
        if isinstance(message, HumanMessage) and isinstance(message.content, list):
            for content_part in message.content:
                if isinstance(content_part, dict) and content_part.get("type") == "image":
                    if content_part.get("source_type") == "url":
                        image_urls.append(content_part.get("url"))
                    elif content_part.get("source_type") == "base64":
                        mime_type = content_part.get("mime_type", "image/jpeg")
                        data = content_part.get("data")
                        image_urls.append(f"data:{mime_type};base64,{data}")
    return image_urls


def extract_image_base64_from_response(response_content: list) -> str:
    """Extract base64 image data from LLM response content"""
    for part in response_content:
        if isinstance(part, dict):
            if "image_url" in part and "url" in part["image_url"]:
                image_data_url = part["image_url"]["url"]
                return image_data_url.split(",")[-1]
            elif "inline_data" in part:
                return part["inline_data"].get("data", "")

    raise ValueError(f"No image found in response: {response_content}")


def ensure_pydantic_model(data: T | dict | None, model_class: Type[T]) -> T | None:
    """
    Convert dict to Pydantic model if needed (LangGraph deserializes to dict).

    Args:
        data: Either a Pydantic model instance, dict, or None
        model_class: The Pydantic model class to convert to

    Returns:
        Pydantic model instance or None
    """
    if data is None:
        return None
    if isinstance(data, dict):
        return model_class(**data)
    return data
