import tempfile
from pathlib import Path
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.schemas.state import State, Step
from src.schemas.seed_image import SeedImageData
from src.config import settings


def extract_image_urls(state: State) -> list[str]:
    image_urls = []
    for message in state["messages"]:
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


def get_art_style_for_age(age: int) -> str:
    """Determine art style based on child's age."""
    if age <= 3:
        return "Simple, bold shapes with bright primary colors. Very minimal details, chunky proportions."
    elif age <= 5:
        return "Colorful storybook illustration with friendly characters. Soft lines, expressive faces."
    elif age <= 8:
        return "Detailed children's book illustration. Rich colors, engaging expressions, moderate detail."
    else:
        return "Chapter book illustration style. More realistic proportions, nuanced expressions, good detail."


def seed_image_node(state: State) -> State:
    llm_image = ChatGoogleGenerativeAI(
        google_api_key=settings.google_api_key,
        model=settings.seed_image.model,
        temperature=settings.seed_image.temperature,
        max_output_tokens=settings.seed_image.max_tokens,
    )

    llm_conversational = ChatGoogleGenerativeAI(
        google_api_key=settings.google_api_key,
        model=settings.seed_image.model,
        temperature=settings.seed_image.temperature,
    )

    image_urls = extract_image_urls(state)

    if not image_urls:
        follow_up = llm_conversational.invoke(
            [
                SystemMessage(
                    content=f"The parent has provided information about their child ({state['challenge'].child.name}, age {state['challenge'].child.age}). "
                    "To create a character reference image, you need at least one photo of the child. "
                    "Ask the parent warmly to upload a clear, recent photo of their child. "
                    "Explain this will help create a personalized character illustration. "
                    "Keep it brief and friendly."
                ),
                *state["messages"],
            ]
        )

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.SEED_IMAGE_GENERATION,
        }

    try:
        system_prompt = build_system_prompt(state["challenge"])

        content_parts = [{"type": "text", "text": system_prompt}]

        for image_url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": image_url}})

        multimodal_message = HumanMessage(content=content_parts)

        llm_image.invoke([multimodal_message])

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_path = Path(temp_file.name)

        seed_image_data = SeedImageData(
            image_path=str(temp_path),
            prompt_used=system_prompt,
        )

        return {
            **state,
            "seed_image": seed_image_data,
            "current_step": Step.COMPLETE,
        }

    except Exception as e:
        follow_up = llm_conversational.invoke(
            [
                SystemMessage(
                    content=f"There was an issue generating the character image: {str(e)}. "
                    "Ask the parent to upload a different or clearer photo of their child. "
                    "Be warm and reassuring. Keep it brief."
                ),
                *state["messages"],
            ]
        )

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.SEED_IMAGE_GENERATION,
        }
