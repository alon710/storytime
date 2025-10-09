from langchain_core.messages import HumanMessage


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
