from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import BaseModel
from typing import Literal
from core.settings import settings
from core.logger import logger


class ChatResponse(BaseModel):
    message: str
    status: Literal["success", "error"] = "success"


class PirateAgent:
    def __init__(self):
        logger.info("Initializing PirateAgent.", model=settings.conversational_agent.model_name)

        self.llm = ChatOpenAI(
            openai_api_key=settings.conversational_agent.api_key.get_secret_value(),  # type: ignore
            model=settings.conversational_agent.model_name,  # type: ignore
            temperature=0.8,
        )

        logger.info("PirateAgent initialized successfully.")

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    template="""You are Captain Blackbeard, a legendary pirate with a colorful personality.
            You speak in classic pirate dialect with phrases like 'Ahoy matey!', 'Arrr!', 'Shiver me timbers!',
            and 'Batten down the hatches!'. You tell tales of the high seas, treasure hunting, and adventures.
            Always stay in character as a friendly but mischievous pirate captain."""
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template(template="{input}"),
            ]
        )

        base_chain = self.prompt | self.llm

        self.chain = RunnableWithMessageHistory(
            runnable=base_chain,
            get_session_history=lambda session_id: SQLChatMessageHistory(
                session_id=session_id, connection_string="sqlite:///chat_history.db"
            ),
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def chat(self, message: str, session_id: str = "default") -> ChatResponse:
        logger.info("Processing chat message.", session_id=session_id)
        try:
            config = {"configurable": {"session_id": session_id}}
            response = self.chain.invoke({"input": message}, config=config)
            logger.info("Chat response generated successfully.")
            return ChatResponse(message=response.content)
        except Exception as e:
            logger.error("Chat processing failed.", error=str(e), error_type=type(e).__name__)
            return ChatResponse(message=f"Arrr, something went wrong: {str(e)}", status="error")
