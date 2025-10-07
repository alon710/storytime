import json
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from src.schemas.state import State
from src.config import settings
from src.schemas.challenge import ChallengeData


def challenge_discovery_node(state: State) -> State:
    llm = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
    )

    system_msg = SystemMessage(content=settings.challenge_discovery.system_prompt)

    filtered_messages = []
    for msg in state["messages"]:
        if hasattr(msg, "content") and isinstance(msg.content, list):
            text_parts = [
                block.get("text", "")
                for block in msg.content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            if text_parts:
                new_msg = (
                    HumanMessage(content=" ".join(text_parts))
                    if msg.type == "human"
                    else AIMessage(content=" ".join(text_parts))
                )
                filtered_messages.append(new_msg)
        else:
            filtered_messages.append(msg)

    response = llm.invoke([system_msg] + filtered_messages)

    challenge_data = None
    try:
        json_match = re.search(r"\{.*?\}", str(response.content), re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            challenge_data = ChallengeData(**data)  # type: ignore
    except Exception:
        pass

    new_state = {**state, "messages": state["messages"] + [response]}

    if challenge_data:
        new_state.update(
            {
                "child_name": challenge_data.child_name,
                "child_age": challenge_data.child_age,
                "child_gender": challenge_data.child_gender,
                "challenge_description": challenge_data.challenge_description,
                "additional_context": challenge_data.additional_context,
                "current_step": "seed_image_generation",
            }
        )

    return new_state
