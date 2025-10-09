import tempfile
from pathlib import Path
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from src.schemas.state import State, Step
from src.schemas.seed_image import SeedImageData
from src.config import settings


def seed_image_node(state: State) -> State:
    llm_image = ChatGoogleGenerativeAI(
        google_api_key=settings.google_api_key,
        model=settings.seed_image.model,
        temperature=settings.seed_image.temperature,
        max_output_tokens=settings.seed_image.max_tokens,
        name="SEED_IMAGE_GENERATION_LLM",
    )

    llm_conversational = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
        name="SEED_IMAGE_CONVERSATIONAL_LLM",
    )

    image_urls = state

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
        content_parts = [{"type": "text", "text": settings.seed_image.system_prompt}]

        for image_url in image_urls:
            content_parts.append({"type": "image_url", "image_url": {"url": image_url}})

        multimodal_message = HumanMessage(content=content_parts)

        llm_image.invoke([multimodal_message])

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_path = Path(temp_file.name)

        seed_image_data = SeedImageData(
            image_path=str(temp_path),
            prompt_used=settings.seed_image.system_prompt,
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
