from langchain_core.messages import AIMessage
from src.schemas.state import State


def seed_image_node(state: State) -> State:
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content="Failed to generate image. Please try again.")],
    }
