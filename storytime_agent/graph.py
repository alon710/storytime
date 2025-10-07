from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from storytime_agent.state import State
from storytime_agent.nodes import discovery_node, seed_image_node


def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("discovery", discovery_node)
    workflow.add_node("seed_image", seed_image_node)

    workflow.set_entry_point("discovery")

    workflow.add_conditional_edges(
        "discovery",
        lambda s: "seed_image" if s.get("child_name") else END,
        {END: END, "seed_image": "seed_image"},
    )

    workflow.add_edge("seed_image", END)

    checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
    return workflow.compile(checkpointer=checkpointer)


graph = build_graph()

__all__ = ["graph", "build_graph"]
