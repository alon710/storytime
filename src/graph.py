from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
from src.schemas.state import State
from src.nodes.challenge_discovery import challenge_discovery_node
from src.nodes.seed_image import seed_image_node


def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("discovery", challenge_discovery_node)
    workflow.add_node("seed_image", seed_image_node)

    workflow.add_edge(START, "discovery")
    workflow.add_edge("discovery", "seed_image")
    workflow.add_edge("seed_image", END)

    return workflow.compile(checkpointer=InMemorySaver())


graph = build_graph()

__all__ = ["graph", "build_graph"]
