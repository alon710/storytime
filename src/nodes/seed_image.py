import logging
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from src.schemas.state import State
from src.schemas.seed_image import SeedImageData
from src.config import settings
from src.nodes.utils import filter_image_content, extract_image_urls
from src.tools.image_generator import generate_image
from src.file_store import temp_file_manager

logger = logging.getLogger(__name__)


def validate_required_fields(seed_image_data: SeedImageData) -> None:
    fields = {
        "img_path": seed_image_data.image_path,
        "approved": seed_image_data.approved,
    }

    for k, v in fields.items():
        if not v:
            raise ValueError(f"Missing required field: {k}")


def seed_image_node(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    seed_image = state.get("seed_image")
    last_message = state["messages"][-1] if state["messages"] else None

    if seed_image and seed_image.approved:
        return {"next": "complete"}

    if isinstance(last_message, AIMessage):
        return {"next": "complete"}

    llm_conversational = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.seed_image.conversational_model,
        temperature=settings.seed_image.temperature,
        name="SEED_IMAGE_CONVERSATIONAL_LLM",
    )

    system_msg = SystemMessage(content=settings.seed_image.system_prompt)

    image_urls = extract_image_urls(state["messages"])

    if not image_urls:
        filtered_messages = filter_image_content(state["messages"])
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
            + filtered_messages
        )

        return {
            "messages": [AIMessage(content=follow_up.content)],
            "next": "retry",
        }

    try:
        logger.info(f"Generating seed image with {len(image_urls)} reference images")

        result = generate_image(
            prompt=settings.seed_image.system_prompt,
            reference_image_urls=image_urls,
            api_key=settings.google_api_key.get_secret_value(),
            model=settings.seed_image.model,
            temperature=settings.seed_image.temperature,
            max_output_tokens=settings.seed_image.max_tokens,
        )

        image_path = temp_file_manager.create_temp_file_from_base64(
            base64_data=result.image_base64, mime_type=result.mime_type, prefix="seed_image_"
        )

        seed_image_data = SeedImageData(
            image_path=image_path, prompt_used=result.prompt_used, mime_type=result.mime_type
        )
        validate_required_fields(seed_image_data)

        image_base64_str = result.image_base64
        response_message = AIMessage(
            content=[
                {
                    "type": "text",
                    "text": f"I've created a character reference image for {state['challenge'].child.name}! Here it is:",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{result.mime_type};base64,{image_base64_str}"},
                },
            ]
        )

        return {
            "seed_image": seed_image_data,
            "messages": [response_message],
            "next": "retry",
        }

    except Exception as e:
        logger.error(f"Error in seed_image_node: {type(e).__name__}: {str(e)}", exc_info=True)
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
            "messages": [AIMessage(content=follow_up.content)],
            "next": "retry",
        }
