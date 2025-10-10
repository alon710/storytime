from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from src.schemas.state import State
from src.config import settings
from src.schemas.book import BookData


def validate_required_fields(book_data: BookData) -> None:
    if not book_data.pages:
        raise ValueError("Missing required field: pages")

    for i, page in enumerate(book_data.pages):
        if not page.title:
            raise ValueError(f"Missing required field: pages[{i}].title")
        if not page.content:
            raise ValueError(f"Missing required field: pages[{i}].content")
        if not page.scene_description:
            raise ValueError(f"Missing required field: pages[{i}].scene_description")


def narrator_node(
    state: State, config: RunnableConfig, *, store: BaseStore
) -> dict:
    """
    Generate therapeutic book content.

    Returns:
        - "continue": Book approved, move to next step
        - "retry": Need to regenerate or wait for approval
        - "complete": End workflow (if last message was AI - avoid loops)
    """
    book = state.get("book")
    last_message = state["messages"][-1] if state["messages"] else None

    # If book is approved, move to next step
    if book and book.approved:
        return {"next": "continue"}

    # If last message was from AI, end to avoid loops
    if isinstance(last_message, AIMessage):
        return {"next": "complete"}

    llm_structured = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.narrator.model,
        temperature=settings.narrator.temperature,
        max_tokens=settings.narrator.max_tokens,
        name="NARRATOR_GENERATION_LLM",
    ).with_structured_output(BookData)

    llm_conversational = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model_name=settings.narrator.model,
        temperature=settings.narrator.temperature,
        name="NARRATOR_CONVERSATIONAL_LLM",
    )

    system_msg = SystemMessage(content=settings.narrator.system_prompt)

    user_msg = SystemMessage(content=f"Context: {state.get('challenge')}")

    try:
        book_data = llm_structured.invoke([system_msg, user_msg])
        validate_required_fields(book_data)

        return {
            "book": book_data,
            "next": "retry",  # Wait for approval
        }

    except Exception as e:
        follow_up = llm_conversational.invoke(
            [
                system_msg,
                user_msg,
                SystemMessage(
                    content=f"There was an issue generating the story: {str(e)}. "
                    "Please let the parent know we'll try again. Be warm and reassuring."
                ),
            ]
        )

        return {
            "messages": [AIMessage(content=follow_up.content)],
            "next": "retry",  # Stay on this node
        }
