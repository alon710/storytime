from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import BaseModel
from typing import Literal, Optional
from core.settings import settings
from core.logger import logger
from core.session import session_context
from core.temp_files import temp_file_manager
from core.workflow_state import workflow_state_manager
from ai.tools.challenge_discovery import discover_challenge
from ai.tools.seed_image_generator import generate_seed_image
from ai.tools.narrator import generate_book_content


class ChatResponse(BaseModel):
    message: str
    images: list[str] | None = None
    status: Literal["success", "error"] = "success"


class ConversationalAgent:
    def __init__(self):
        logger.info("Initializing Agent.", model=settings.conversational_agent.model_name)

        self.llm = ChatOpenAI(
            openai_api_key=settings.conversational_agent.api_key.get_secret_value(),  # type: ignore
            model=settings.conversational_agent.model_name,  # type: ignore
            temperature=settings.conversational_agent.temperature,
        )

        self.tools = [discover_challenge, generate_seed_image, generate_book_content]

        logger.info("ConversationalAgent initialized successfully.", tool_count=len(self.tools))

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", settings.conversational_agent.system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=settings.is_development_mode,
            handle_parsing_errors=True,
        )

        self.chain = RunnableWithMessageHistory(
            runnable=self.agent_executor,
            get_session_history=lambda session_id: SQLChatMessageHistory(
                session_id=session_id,
                connection="sqlite:///chat.db",
            ),
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def chat(self, message: str, files: Optional[list] = None, session_id: str = "default") -> ChatResponse:
        logger.info("Processing chat message.", session_id=session_id, has_files=bool(files))

        try:
            session_context.set_current_session(session_id)
            artifacts = session_context.get_all_artifacts(session_id)
            session_context.clear_artifacts(session_id)
            if "available_images" in artifacts:
                for img_path in artifacts["available_images"]:
                    session_context.add_artifacts("available_images", img_path)

            if files:
                logger.info("Processing uploaded files.", file_count=len(files))
                for file in files:
                    if hasattr(file, "read"):
                        file_content = file.read()
                        temp_path = temp_file_manager.save_file(file_content)
                        session_context.add_artifacts("available_images", temp_path)
                        logger.info(
                            "File processed and saved to temp file.",
                            filename=getattr(file, "name", "unknown"),
                            path=temp_path,
                        )

            # Build enhanced message with workflow state context
            workflow_state = workflow_state_manager.get_workflow_state(session_id)

            # Build workflow context
            workflow_context_parts = [
                "\n\n=== WORKFLOW STATE ===",
                f"Current Step: {workflow_state.current_step}",
            ]

            # Add completed steps info
            completed_steps = []
            if workflow_state.challenge_data:
                completed_steps.append("✓ discovery (Challenge data captured)")
            if workflow_state.seed_image_path:
                completed_steps.append("✓ seed_image (Character reference created)")
            if workflow_state.book_content:
                completed_steps.append(f"✓ narration ({workflow_state.book_content.total_pages}-page book written)")

            if completed_steps:
                workflow_context_parts.append(f"Completed Steps: {', '.join(completed_steps)}")
            else:
                workflow_context_parts.append("Completed Steps: None - this is the start of the workflow")

            # Add next step guidance
            if not workflow_state.challenge_data:
                workflow_context_parts.append("NEXT ACTION: Use discover_challenge tool to gather child's information")
            elif not workflow_state.seed_image_path:
                workflow_context_parts.append("NEXT ACTION: Use generate_seed_image tool with uploaded photo")
            elif not workflow_state.book_content:
                workflow_context_parts.append("NEXT ACTION: Use generate_book_content tool to write the story")
            else:
                workflow_context_parts.append("NEXT ACTION: Illustration and PDF generation (coming soon)")

            workflow_context = "\n".join(workflow_context_parts)

            # Add available images info
            enhanced_message = message
            available_images = session_context.get_artifacts(session_id, "available_images")
            if available_images:
                img_paths = ", ".join(available_images)
                enhanced_message = f"{message}\n\nAvailable images: {img_paths}"

            # Combine message with workflow context
            enhanced_message = f"{enhanced_message}{workflow_context}\n======================\n"

            logger.info(
                "Enhanced message with workflow context",
                session_id=session_id,
                current_step=workflow_state.current_step,
                completed_steps_count=len(completed_steps),
            )

            config = {"configurable": {"session_id": session_id}}
            response = self.chain.invoke({"input": enhanced_message}, config=config)

            artifacts = session_context.get_all_artifacts(session_id)

            return ChatResponse(
                message=response.get("output", ""),
                images=artifacts.get("images"),
                status="success",
            )

        except Exception as e:
            logger.error("Chat processing failed.", error=str(e), error_type=type(e).__name__)
            return ChatResponse(message=f"Something went wrong: {str(e)}", status="error")
