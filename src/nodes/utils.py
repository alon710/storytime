from langchain_core.messages import HumanMessage


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


def extract_image_urls(messages: list) -> list[str]:
    """Extract image URLs from messages, supporting both URL and base64 formats"""
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
