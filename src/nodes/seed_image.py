import base64
import requests
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.schemas.state import State
from src.config import settings


def seed_image_node(state: State) -> State:
    child_name = state.get("child_name", "child")
    child_age = state.get("child_age", 5)
    child_gender = state.get("child_gender", "")
    challenge = state.get("challenge_description", "")

    uploaded_image_url = None
    for msg in reversed(state.get("messages", [])):
        if hasattr(msg, "content") and isinstance(msg.content, list):
            for block in msg.content:
                if isinstance(block, dict) and block.get("type") == "image_url":
                    uploaded_image_url = block["image_url"]["url"]
                    break
        if uploaded_image_url:
            break

    if not uploaded_image_url:
        return {
            **state,
            "messages": state["messages"]
            + [AIMessage(content="Please upload a photo of your child first to generate the character!")],
        }

    if uploaded_image_url.startswith("http"):
        response = requests.get(uploaded_image_url)
        img_base64 = base64.b64encode(response.content).decode()
    else:
        img_base64 = uploaded_image_url.split(",")[1] if "," in uploaded_image_url else uploaded_image_url

    prompt = f"Create hero-style character illustration of {child_name}, age {child_age}, {child_gender}. For therapeutic children's book about: {challenge}. Style: warm, friendly children's book illustration, simple background."

    llm = ChatGoogleGenerativeAI(
        model=settings.seed_image.model,
        google_api_key=settings.google_api_key.get_secret_value(),
        temperature=settings.seed_image.temperature,
        max_output_tokens=settings.seed_image.max_tokens,
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}},
        ]
    )

    result = llm.invoke([message], generation_config={"response_modalities": ["TEXT", "IMAGE"]})

    generated_image = None
    if isinstance(result.content, list):
        for block in result.content:
            if isinstance(block, dict) and "image_url" in block:
                generated_image = block["image_url"]["url"]
                break

    if generated_image:
        return {
            **state,
            "current_step": "complete",
            "messages": state["messages"]
            + [
                AIMessage(
                    content=[
                        {"type": "text", "text": f"Here's the hero character for {child_name}!"},
                        {"type": "image_url", "image_url": {"url": generated_image}},
                    ]
                )
            ],
        }
    else:
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content="Failed to generate image. Please try again.")],
        }
