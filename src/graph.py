from langgraph.graph import StateGraph, END, START
from src.schemas.state import State, Step
from src.nodes.challenge_discovery import challenge_discovery_node
from src.nodes.seed_image import seed_image_node


def route_after_discovery(state: State) -> str:
    if state["current_step"] == Step.SEED_IMAGE_GENERATION:
        return "seed_image"
    return END


def _add_nodes(workflow: StateGraph) -> None:
    workflow.add_node("challenge_discovery", challenge_discovery_node)
    workflow.add_node("seed_image", seed_image_node)


def _add_edges(workflow: StateGraph) -> None:
    workflow.add_edge(START, "challenge_discovery")
    workflow.add_conditional_edges("challenge_discovery", route_after_discovery)
    workflow.add_edge("seed_image", END)


def build_graph():
    workflow: StateGraph = StateGraph(State)

    _add_nodes(workflow=workflow)
    _add_edges(workflow=workflow)

    return workflow.compile()


graph = build_graph()
