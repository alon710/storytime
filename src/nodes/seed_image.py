from base64 import b64decode
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from src.schemas.state import State, Step
from src.schemas.seed_image import SeedImageData
from src.config import settings
from src.nodes.temp_file_handler import get_temp_handler


def validate_required_fields(seed_image_data: SeedImageData) -> None:
    required_fields: list = [
        seed_image_data.image_path,
        seed_image_data.approved,
    ]

    for value in required_fields:
        if not value:
            raise ValidationError("Missing required field")


def seed_image_node(state: State) -> State:
    seed_image = state.get("seed_image")
    last_message = state["messages"][-1] if state["messages"] else None

    if seed_image and seed_image.approved:
        return {
            **state,
            "current_step": Step.COMPLETE,
        }

    if isinstance(last_message, AIMessage):
        return {
            **state,
            "current_step": Step.COMPLETE,
        }

    llm_structured = ChatGoogleGenerativeAI(
        google_api_key=settings.google_api_key,
        model=settings.seed_image.model,
        temperature=settings.seed_image.temperature,
        max_output_tokens=settings.seed_image.max_tokens,
        name="SEED_IMAGE_GENERATION_LLM",
    )

    llm_conversational = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.seed_image.model,
        temperature=settings.seed_image.temperature,
        name="SEED_IMAGE_CONVERSATIONAL_LLM",
    )

    system_msg = SystemMessage(content=settings.seed_image.system_prompt)
    image_urls = extract_image_urls(state["messages"])

    if not image_urls:
        follow_up = llm_conversational.invoke(
            [
                system_msg,
                SystemMessage(
                    content=f"The parent has provided information about their child ({state['challenge'].child.name}, age {state['challenge'].child.age}). "
                    "To create a character reference image, you need at least one photo of the child. "
                    "Ask the parent warmly to upload a clear, recent photo of their child. "
                    "Explain this will help create a personalized character illustration. "
                    "Keep it brief and friendly."
                ),
            ]
            + state["messages"]
        )

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.SEED_IMAGE_GENERATION,
        }

    try:
        content_parts = [{"type": "text", "text": settings.seed_image.system_prompt}]

        for image_url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": image_url}})

        multimodal_message = HumanMessage(content=content_parts)

        response = llm_structured.invoke(
            [multimodal_message], generation_config=dict(response_modalities=["TEXT", "IMAGE"])
        )

        image_base64 = None
        if isinstance(response.content, list):
            for part in response.content:
                if isinstance(part, dict):
                    if "image_url" in part and "url" in part["image_url"]:
                        image_data_url = part["image_url"]["url"]
                        image_base64 = image_data_url.split(",")[-1]
                        break
                    elif "inline_data" in part:
                        image_base64 = part["inline_data"].get("data", "")
                        break
            if not image_base64:
                raise ValueError(f"No image found in response: {response.content}")
        else:
            raise ValueError(f"Unexpected response format: {type(response.content)}")

        img_bytes = b64decode(image_base64)
        temp_handler = get_temp_handler()
        temp_path = temp_handler.write_bytes(img_bytes, suffix=".png", prefix="seed_image_")

        seed_image_data = SeedImageData(
            image_path=str(temp_path),
            prompt_used=settings.seed_image.system_prompt,
        )
        validate_required_fields(seed_image_data)

        return {
            **state,
            "seed_image": seed_image_data,
            "current_step": Step.SEED_IMAGE_GENERATION,
        }

    except Exception as e:
        follow_up = llm_conversational.invoke(
            [
                system_msg,
                SystemMessage(
                    content=f"There was an issue generating the character image: {str(e)}. "
                    "Please let the parent know we'll try again. Be warm and reassuring."
                ),
            ]
        )

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.SEED_IMAGE_GENERATION,
        }
