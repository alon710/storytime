from langgraph.graph import StateGraph, END, START
from src.schemas.state import State, Step
from src.nodes.challenge_discovery import challenge_discovery_node
from src.nodes.seed_image import seed_image_node
from src.nodes.narrator import narrator_node


def route_step(state: State) -> str:
    step = state.get("current_step", Step.CHALLENGE_DISCOVERY)

    routing_map = {
        Step.CHALLENGE_DISCOVERY: "challenge_discovery",
        Step.NARRATION: "narrator",
        Step.SEED_IMAGE_GENERATION: "seed_image",
        Step.COMPLETE: END,
    }

    return routing_map.get(step, END)


def _add_nodes(workflow: StateGraph) -> None:
    workflow.add_node("challenge_discovery", challenge_discovery_node)
    workflow.add_node("narrator", narrator_node)
    workflow.add_node("seed_image", seed_image_node)


def _add_edges(workflow: StateGraph) -> None:
    all_nodes = [
        "challenge_discovery",
        "narrator",
        "seed_image",
    ]

    workflow.add_edge(START, "challenge_discovery")

    for node in all_nodes:
        workflow.add_conditional_edges(
            node,
            route_step,
            {
                "challenge_discovery": "challenge_discovery",
                "seed_image": "seed_image",
                "narrator": "narrator",
                END: END,
            },
        )


def build_graph():
    workflow: StateGraph = StateGraph(State)

    _add_nodes(workflow=workflow)
    _add_edges(workflow=workflow)

    return workflow.compile()


graph = build_graph()
