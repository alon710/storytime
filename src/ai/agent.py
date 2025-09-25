from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
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

        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
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

        self.chain = (
            RunnablePassthrough.assign(chat_history=lambda x: self.memory.chat_memory.messages) | self.prompt | self.llm
        )

    def chat(self, message: str) -> ChatResponse:
        logger.info("Processing chat message.")
        try:
            response = self.chain.invoke({"input": message})
            self.memory.save_context({"input": message}, {"output": response.content})
            logger.info("Chat response generated successfully.", output_length=len(response.content))
            return ChatResponse(message=response.content)
        except Exception as e:
            logger.error("Chat processing failed.", error=str(e), error_type=type(e).__name__)
            return ChatResponse(message=f"Arrr, something went wrong: {str(e)}", status="error")

    async def achat(self, message: str) -> ChatResponse:
        logger.info("Processing async chat message.", input_length=len(message))
        try:
            response = await self.chain.ainvoke({"input": message})
            self.memory.save_context({"input": message}, {"output": response.content})
            logger.info("Async chat response generated successfully.")
            return ChatResponse(message=response.content)
        except Exception as e:
            logger.error("Async chat processing failed.", error=str(e), error_type=type(e).__name__)
            return ChatResponse(message=f"Arrr, something went wrong: {str(e)}", status="error")
