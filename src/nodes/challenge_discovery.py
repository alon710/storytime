from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from src.schemas.state import State, Step
from src.config import settings
from src.schemas.challenge import ChallengeData


def validate_required_fields(challenge_data: ChallengeData) -> None:
    required_fields: list = [challenge_data.child.name, challenge_data.child.age, challenge_data.challenge_description]

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
    messages = [system_msg] + state["messages"]

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
                    content="Ask the parent for missing information in a friendly way. Keep the conversation natural."
                ),
            ]
            + state["messages"]
        )

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.CHALLENGE_DISCOVERY,
        }
