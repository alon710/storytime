from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from src.schemas.state import State, NextAction
from src.config import settings
from src.schemas.challenge import ChallengeData
from src.nodes.utils import ensure_pydantic_model, filter_image_content


def validate_required_fields(challenge_data: ChallengeData) -> None:
    fields = {
        "child_name": challenge_data.child.name,
        "child_age": challenge_data.child.age,
        "child_gender": challenge_data.child.gender,
        "challenge_description": challenge_data.challenge_description,
        "details_approved": challenge_data.approved,
    }

    for k, v in fields.items():
        if not v:
            raise ValueError(f"Missing required field: {k}")


def challenge_discovery_node(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    challenge = ensure_pydantic_model(state.get("challenge"), ChallengeData)
    last_message = state["messages"][-1] if state["messages"] else None

    if challenge and challenge.approved:
        return {"next_action": NextAction.CONTINUE}

    if isinstance(last_message, AIMessage):
        return {"next_action": NextAction.END}

    llm_structured = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
        name="CHALLENGE_EXTRACTION_LLM",
    ).with_structured_output(schema=ChallengeData)

    llm_conversational = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
        name="CHALLENGE_CONVERSATIONAL_LLM",
    )

    system_msg = SystemMessage(content=settings.challenge_discovery.system_prompt)
    messages = [system_msg] + state["messages"]

    try:
        challenge_data = llm_structured.invoke(input=messages)
        validate_required_fields(challenge_data=challenge_data)

        return {
            "challenge": challenge_data,
            "next_action": NextAction.RETRY,
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
            + filter_image_content(state["messages"])
        )

        return {
            "messages": [AIMessage(content=follow_up.content)],
            "next_action": NextAction.RETRY,
        }
