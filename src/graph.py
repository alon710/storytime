from langgraph.graph import StateGraph, START, END
from src.schemas.state import State
from src.nodes.challenge_discovery import challenge_discovery_node
from src.nodes.seed_image import seed_image_node
from src.nodes.narrator import narrator_node


def build_graph():
    workflow: StateGraph = StateGraph(state_schema=State)

    workflow.add_node(node="challenge_discovery", action=challenge_discovery_node)
    workflow.add_node(node="narrator", action=narrator_node)
    workflow.add_node(node="seed_image", action=seed_image_node)

    workflow.add_edge(start_key=START, end_key="challenge_discovery")
    workflow.add_edge(start_key="challenge_discovery", end_key="seed_image")
    workflow.add_edge(start_key="seed_image", end_key="narrator")
    workflow.add_edge(start_key="narrator", end_key=END)

    return workflow.compile()


graph = build_graph()
