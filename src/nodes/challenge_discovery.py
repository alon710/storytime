from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from src.schemas.state import State, Step
from src.config import settings
from src.schemas.challenge import ChallengeData


def filter_image_content(messages: list) -> list:
    filtered = []
    for msg in messages:
        if isinstance(msg, HumanMessage) and isinstance(msg.content, list):
            text_content = [item for item in msg.content if item.get("type") == "text"]
            if text_content:
                filtered.append(HumanMessage(content=text_content))
        else:
            filtered.append(msg)
    return filtered


def validate_required_fields(challenge_data: ChallengeData) -> None:
    required_fields: list = [
        challenge_data.child.name,
        challenge_data.child.age,
        challenge_data.child.gender,
        challenge_data.challenge_description,
    ]

    for value in required_fields:
        if not value:
            raise ValidationError("Missing required field")


def challenge_discovery_node(state: State) -> State:
    llm_structured = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
    ).with_structured_output(ChallengeData)

    llm_conversational = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
    )

    system_msg = SystemMessage(content=settings.challenge_discovery.system_prompt)

    filtered_messages = filter_image_content(state["messages"])
    messages = [system_msg] + filtered_messages

    try:
        challenge_data = llm_structured.invoke(input=messages)
        validate_required_fields(challenge_data=challenge_data)

        return {
            **state,
            "challenge": challenge_data,
            "current_step": Step.SEED_IMAGE_GENERATION,
        }

    except Exception:
        follow_up = llm_conversational.invoke(
            [
                system_msg,
                SystemMessage(
                    content="The parent hasn't provided all required information yet. "
                    "Ask ONE specific question to gather the missing details. "
                    "Be warm and friendly. Do NOT provide solutions or mention next steps."
                ),
            ]
            + filtered_messages
        )

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.CHALLENGE_DISCOVERY,
        }
