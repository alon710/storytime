from base64 import b64decode
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from src.schemas.state import State, Step
from src.schemas.seed_image import SeedImageData
from src.config import settings
from src.nodes.utils import classify_approval_intent, ApprovalIntent, filter_image_content, get_approval_llm
from src.nodes.temp_file_handler import get_temp_handler


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


def seed_image_node(state: State) -> State:
    seed_image = state.get("seed_image")
    last_message = state["messages"][-1] if state["messages"] else None

    if seed_image and seed_image.approved:
        return {
            **state,
            "current_step": Step.COMPLETE,
        }

    if seed_image and not seed_image.approved:
        if isinstance(last_message, AIMessage):
            return {
                **state,
                "current_step": Step.COMPLETE,
            }

        llm = get_approval_llm("SEED_IMAGE_APPROVAL_LLM")

        classification = classify_approval_intent(
            user_message=last_message.content if last_message else "",
            context="the generated character reference image",
            llm=llm
        )

        filtered_messages = filter_image_content(state["messages"])

        if classification.intent == ApprovalIntent.APPROVE:
            seed_image.approved = True
            response = llm.invoke([
                SystemMessage(
                    content="The parent has approved the character reference image. "
                    "Thank them warmly and let them know the book is complete. Keep it brief and celebratory."
                ),
                *filtered_messages,
            ])
            return {
                **state,
                "seed_image": seed_image,
                "messages": state["messages"] + [AIMessage(content=response.content)],
                "current_step": Step.COMPLETE,
            }

        elif classification.intent == ApprovalIntent.REJECT:
            response = llm.invoke([
                SystemMessage(
                    content="The parent wants a different character image. "
                    "Ask them what specifically they'd like to change about the illustration. "
                    "Be understanding and supportive."
                ),
                *filtered_messages,
            ])
            return {
                **state,
                "seed_image": None,
                "messages": state["messages"] + [AIMessage(content=response.content)],
                "current_step": Step.SEED_IMAGE_GENERATION,
            }

        else:
            response = llm.invoke([
                SystemMessage(
                    content=f"The parent's response about the character illustration was unclear. "
                    f"The character image is saved at: {seed_image.image_path}\n\n"
                    "Politely ask them for a clear yes/no on whether they approve the illustration. "
                    "Be warm and encouraging."
                ),
                *filtered_messages,
            ])
            return {
                **state,
                "messages": state["messages"] + [AIMessage(content=response.content)],
                "current_step": Step.SEED_IMAGE_GENERATION,
            }

    if isinstance(last_message, AIMessage):
        return {
            **state,
            "current_step": Step.COMPLETE,
        }

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

    image_urls = extract_image_urls(state)

    if not image_urls:
        filtered_messages = filter_image_content(state["messages"])
        follow_up = llm_conversational.invoke(
            [
                SystemMessage(
                    content=f"The parent has provided information about their child ({state['challenge'].child.name}, age {state['challenge'].child.age}). "
                    "To create a character reference image, you need at least one photo of the child. "
                    "Ask the parent warmly to upload a clear, recent photo of their child. "
                    "Explain this will help create a personalized character illustration. "
                    "Keep it brief and friendly."
                ),
                *filtered_messages,
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

        response = llm_image.invoke(
            [multimodal_message],
            generation_config=dict(response_modalities=["TEXT", "IMAGE"])
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

        filtered_messages = filter_image_content(state["messages"])
        approval_message = llm_conversational.invoke(
            [
                SystemMessage(
                    content=f"You've just generated a character illustration for {state['challenge'].child.name}. "
                    f"The image has been saved at {temp_path} and will be shown to the parent. "
                    "Write a warm, brief message asking the parent to review the character illustration "
                    "and let you know if they approve it or would like changes. Keep it conversational and friendly."
                ),
                *filtered_messages,
            ]
        )

        return {
            **state,
            "seed_image": seed_image_data,
            "messages": state["messages"] + [AIMessage(content=approval_message.content)],
            "current_step": Step.SEED_IMAGE_GENERATION,
        }

    except Exception as e:
        filtered_messages = filter_image_content(state["messages"])
        follow_up = llm_conversational.invoke(
            [
                SystemMessage(
                    content=f"There was an issue generating the character image: {str(e)}. "
                    "Ask the parent to upload a different or clearer photo of their child. "
                    "Be warm and reassuring. Keep it brief."
                ),
                *filtered_messages,
            ]
        )

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.SEED_IMAGE_GENERATION,
        }
