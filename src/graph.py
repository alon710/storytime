from langgraph.graph import StateGraph, END, START
from src.schemas.state import State
from src.nodes.challenge_discovery import challenge_discovery_node
from src.nodes.seed_image import seed_image_node


def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("challenge_discovery", challenge_discovery_node)
    workflow.add_node("seed_image", seed_image_node)

    workflow.add_edge(START, "challenge_discovery")
    workflow.add_edge("challenge_discovery", "seed_image")
    workflow.add_edge("seed_image", END)

    return workflow.compile()


graph = build_graph()
