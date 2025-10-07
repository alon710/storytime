from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from src.schemas.state import State, Step
from src.config import settings
from src.schemas.challenge import ChallengeData


def challenge_discovery_node(state: State) -> State:
    llm = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.challenge_discovery.model,
        temperature=settings.challenge_discovery.temperature,
    ).with_structured_output(ChallengeData)

    system_msg = SystemMessage(content=settings.challenge_discovery.system_prompt)

    challenge_data = llm.invoke([system_msg] + state["messages"])

    return {
        **state,
        "challenge": challenge_data,
        "current_step": Step.SEED_IMAGE_GENERATION,
    }
