from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from src.schemas.state import State, Step
from src.config import settings
from src.schemas.book import BookData


def validate_required_fields(book_data: BookData) -> None:
    required_fields: list = [
        book_data.pages,
        book_data.approved,
    ]

    for value in required_fields:
        if not value:
            raise ValidationError("Missing required field")

    for page in book_data.pages:
        if not page.title or not page.content or not page.scene_description:
            raise ValidationError("Missing required page fields")


def narrator_node(state: State) -> State:
    book = state.get("book")
    last_message = state["messages"][-1] if state["messages"] else None

    if book and book.approved:
        return {
            **state,
            "current_step": Step.SEED_IMAGE_GENERATION,
        }

    if isinstance(last_message, AIMessage):
        return {
            **state,
            "current_step": Step.COMPLETE,
        }

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
            **state,
            "book": book_data,
            "current_step": Step.NARRATION,
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
            **state,
            "messages": state["messages"] + [AIMessage(content=follow_up.content)],
            "current_step": Step.NARRATION,
        }
