from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from src.schemas.state import State, Step
from src.config import settings
from src.schemas.challenge import ChallengeData
from src.nodes.utils import filter_image_content


def validate_required_fields(challenge_data: ChallengeData) -> None:
    required_fields: list = [
        challenge_data.child.name,
        challenge_data.child.age,
        challenge_data.child.gender,
        challenge_data.challenge_description,
        challenge_data.approved,
    ]

    for value in required_fields:
        if not value:
            raise ValidationError("Missing required field")


def challenge_discovery_node(state: State) -> State:
    challenge = state.get("challenge")
    last_message = state["messages"][-1] if state["messages"] else None

    if challenge and challenge.approved:
        return {
            **state,
            "current_step": Step.NARRATION,
        }

    if isinstance(last_message, AIMessage):
        return {
            **state,
            "current_step": Step.COMPLETE,
        }

    llm_structured = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
        name="CHALLENGE_EXTRACTION_LLM",
    ).with_structured_output(ChallengeData)

    llm_conversational = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
        name="CHALLENGE_CONVERSATIONAL_LLM",
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
            "current_step": Step.CHALLENGE_DISCOVERY,
        }

    except Exception:
        follow_up = llm_conversational.invoke(
            [
                system_msg,
                SystemMessage(
                    content="The parent hasn't provided all required information yet. "
                    "Ask ONE specific question to gather the missing details. "
                    "Be warm and friendly. DO NOT provide solutions or mention next steps."
                ),
            ]
            + filtered_messages
        )

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.CHALLENGE_DISCOVERY,
        }
