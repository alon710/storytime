from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import structlog

from app.settings import settings
from app.database.session_manager import SessionManager
from app.tools.seed import SeedTool
from app.tools.narrator import NarratorTool
from app.tools.illustrator import IllustratorTool

logger = structlog.get_logger()


class StoryTimeConversationalAgent:
    def __init__(self):
        self.session_manager = SessionManager()
        self.logger = logger.bind(component="conversational_agent")

        self.llm = ChatOpenAI(
            model_name=settings.main_agent_model,
            temperature=0.7,
            streaming=True,
            api_key=settings.openai_api_key
        )

        self.tools = [
            SeedTool(settings.seed_model),
            NarratorTool(settings.narrator_model),
            IllustratorTool(settings.illustrator_model),
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def initialize(self) -> None:
        await self.session_manager.initialize()
        self.logger.info("Conversational agent initialized")

    def _get_system_prompt(self) -> str:
        return """You are StoryTime, a friendly AI assistant that helps create personalized children's books.

Your role is to:
1. Have natural conversations with users to collect information about their child
2. Gather the following required information:
   - Child's name
   - Child's age (3-8 years old)
   - Child's gender
   - Challenge or theme for the story (what the child is struggling with or wants to learn)

3. When you have ALL required information, use your tools to:
   - Generate seed images for characters
   - Create the personalized story
   - Generate illustrations
   - Save everything

CONVERSATION GUIDELINES:
- Be warm, friendly, and encouraging
- Ask one question at a time
- Validate information naturally (e.g., "So Emma is 5 years old, is that right?")
- If information is missing or unclear, ask follow-up questions
- Keep track of what you've learned in each session
- When ready to generate, explain what you're doing

IMPORTANT: Only call tools when you have collected ALL required information from the user.
If any information is missing, continue the conversation to gather it naturally.

Always check the session data to see what information has already been collected before asking questions."""

    async def chat(self, session_id: str, user_message: str) -> str:
        try:
            await self.session_manager.add_chat_message(session_id, "human", user_message)

            session_data = await self.session_manager.get_session_data(session_id)
            missing_fields = await self.session_manager.get_missing_fields(session_id)

            chat_history = await self.session_manager.get_chat_history(session_id)
            history_messages = []
            for msg in chat_history[:-1]:  # Exclude the current message
                if msg.role == "human":
                    history_messages.append(HumanMessage(content=msg.content))
                else:
                    history_messages.append(AIMessage(content=msg.content))

            context = self._build_context(session_data, missing_fields)

            response = await self.executor.ainvoke({
                "input": f"{context}\n\nUser message: {user_message}",
                "chat_history": history_messages
            })

            ai_response = response["output"]

            await self.session_manager.add_chat_message(session_id, "assistant", ai_response)

            await self._extract_and_update_session_data(session_id, user_message, ai_response)

            return ai_response

        except Exception as e:
            self.logger.error("Chat processing failed", error=str(e), session_id=session_id)
            return "I'm sorry, I encountered an error. Could you please try again?"

    def _build_context(self, session_data, missing_fields: list[str]) -> str:
        context_parts = ["Session Context:"]

        if session_data:
            if session_data.child_name:
                context_parts.append(f"- Child's name: {session_data.child_name}")
            if session_data.child_age:
                context_parts.append(f"- Child's age: {session_data.child_age}")
            if session_data.child_gender:
                context_parts.append(f"- Child's gender: {session_data.child_gender}")
            if session_data.challenge_theme:
                context_parts.append(f"- Challenge/theme: {session_data.challenge_theme}")

        if missing_fields:
            context_parts.append(f"- Still need to collect: {', '.join(missing_fields)}")

        if not missing_fields:
            context_parts.append("- ✅ ALL INFORMATION COLLECTED - Ready to generate story!")

        return "\n".join(context_parts)

    async def _extract_and_update_session_data(self, session_id: str, user_message: str, ai_response: str) -> None:
        import re

        updates = {}

        if "name" in user_message.lower():
            name_match = re.search(r'(?:name is|called|i\'?m)\s+([A-Za-z]+)', user_message, re.IGNORECASE)
            if name_match:
                updates["child_name"] = name_match.group(1).capitalize()

        if "old" in user_message.lower() or "age" in user_message.lower():
            age_match = re.search(r'\b([3-8])\b', user_message)
            if age_match:
                updates["child_age"] = int(age_match.group(1))

        gender_words = {"boy": "boy", "girl": "girl", "he": "boy", "she": "girl", "him": "boy", "her": "girl"}
        for word, gender in gender_words.items():
            if word in user_message.lower():
                updates["child_gender"] = gender
                break

        if any(word in user_message.lower() for word in ["scared", "afraid", "shy", "angry", "sharing", "bedtime", "potty"]):
            updates["challenge_theme"] = user_message

        if updates:
            await self.session_manager.update_session_data(session_id, **updates)

    async def create_new_session(self) -> str:
        return await self.session_manager.create_session()