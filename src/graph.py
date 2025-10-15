from langgraph.graph import StateGraph, START, END
from src.schemas.state import State
from src.nodes.challenge_discovery import challenge_discovery_node
from src.nodes.seed_image import seed_image_node
from src.nodes.narrator import narrator_node
from src.schemas.state import NextAction


def route_node(state: State) -> str:
    next_action = state.get("next_action", NextAction.CONTINUE)

    if next_action == NextAction.CONTINUE:
        return NextAction.CONTINUE
    elif next_action == NextAction.RETRY:
        return NextAction.RETRY
    else:
        return NextAction.END


def build_graph():
    workflow: StateGraph = StateGraph(state_schema=State)

    workflow.add_node(node="challenge_discovery", action=challenge_discovery_node)
    workflow.add_node(node="seed_image", action=seed_image_node)
    workflow.add_node(node="narrator", action=narrator_node)

    workflow.add_edge(start_key=START, end_key="challenge_discovery")

    workflow.add_conditional_edges(
        source="challenge_discovery",
        path=route_node,
        path_map={
            "continue": "seed_image",
            "retry": "challenge_discovery",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        source="seed_image",
        path=route_node,
        path_map={
            "continue": "narrator",
            "retry": "seed_image",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        source="narrator",
        path=route_node,
        path_map={
            "continue": END,
            "retry": "narrator",
            END: END,
        },
    )

    return workflow.compile()


graph = build_graph()
