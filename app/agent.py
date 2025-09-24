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
            api_key=settings.openai_api_key,
        )

        self.tools = [
            SeedTool(settings.seed_model),
            NarratorTool(settings.narrator_model),
            IllustratorTool(settings.illustrator_model),
        ]

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._get_system_prompt()),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def initialize(self) -> None:
        await self.session_manager.initialize()
        self.logger.info("Conversational agent initialized")

    def _get_system_prompt(self) -> str:
        return """You are StoryTime, a friendly AI assistant that helps create personalized children's books.

Your role is to:
1. Have natural conversations with users to collect information about their child
2. Gather the following REQUIRED information:
   - Child's name
   - Child's age
   - Child's gender
   - Challenge or theme for the story (what the child is struggling with or wants to learn)
   - Reference images of the child (REQUIRED - at least one clear photo)

3. REFERENCE IMAGES (REQUIRED):
   - At least one clear photo of the child is REQUIRED before proceeding
   - Encourage parents to upload the best photo of their child's face
   - Explain that this helps create accurate, personalized illustrations
   - If they mention toys, dolls, pets, suggest uploading those photos too for extra characters

4. TWO-PHASE WORKFLOW:

   PHASE 1: Information Collection + Seed Generation
   - When you have ALL required info including child's photo, generate a seed image
   - Show the generated seed image to the parent
   - Ask: "Does this look like [child's name]? Should I proceed with creating the story?"
   - DO NOT proceed to story generation until parent approves

   PHASE 2: Story Generation (ONLY after seed approval)
   - If parent approves seed: proceed with story creation
   - If parent rejects seed: regenerate with their feedback
   - Allow parents to request adjustments to the seed image

CONVERSATION GUIDELINES:
- Be warm, friendly, and encouraging
- Ask one question at a time
- Validate information naturally (e.g., "So Emma is 5 years old, is that right?")
- ALWAYS require at least one photo of the child before proceeding
- When ready for seed generation, explain what you're doing
- Show seed image and wait for approval before story generation
- Handle approval/rejection responses naturally

IMPORTANT:
- Reference images of the child are MANDATORY (not optional)
- Only generate seed when ALL info including photos is collected
- Only proceed to story generation after seed is approved
- Check session data for what's been collected and approval status
- ALWAYS pass the session_id when calling any tool so it can access stored images and data

Always check the session data to see what information has already been collected and approval status before asking questions."""

    async def chat(
        self, session_id: str, user_message: str, reference_images: list | None = None
    ) -> str:
        try:
            await self.session_manager.add_chat_message(
                session_id, "human", user_message
            )

            # Store reference images in session if provided
            if reference_images:
                await self.session_manager.store_reference_images(
                    session_id, reference_images
                )
                self.logger.info(
                    "Stored reference images",
                    session_id=session_id,
                    count=len(reference_images),
                )

            # Get updated session data and missing fields AFTER storing images
            session_data = await self.session_manager.get_session_data(session_id)
            missing_fields = await self.session_manager.get_missing_fields(session_id)
            seed_status = await self.session_manager.get_seed_approval_status(
                session_id
            )

            # Get ALL stored reference images from database
            all_stored_images = await self.session_manager.get_reference_images(session_id)

            chat_history = await self.session_manager.get_chat_history(session_id)
            history_messages = []
            for msg in chat_history[:-1]:  # Exclude the current message
                if msg.role == "human":
                    history_messages.append(HumanMessage(content=msg.content))
                else:
                    history_messages.append(AIMessage(content=msg.content))

            context = self._build_context(
                session_data, missing_fields, all_stored_images, seed_status
            )

            response = await self.executor.ainvoke(
                {
                    "input": f"{context}\n\nSession ID: {session_id}\n\nUser message: {user_message}",
                    "chat_history": history_messages,
                    "session_id": session_id,
                }
            )

            ai_response = response["output"]

            await self.session_manager.add_chat_message(
                session_id, "assistant", ai_response
            )

            await self._extract_and_update_session_data(
                session_id, user_message, ai_response
            )

            return ai_response

        except Exception as e:
            self.logger.error(
                "Chat processing failed", error=str(e), session_id=session_id
            )
            return "I'm sorry, I encountered an error. Could you please try again?"

    def _build_context(
        self,
        session_data,
        missing_fields: list[str],
        reference_images: list | None = None,
        seed_status: dict | None = None,
    ) -> str:
        context_parts = ["Session Context:"]

        if session_data:
            if session_data.child_name:
                context_parts.append(f"- Child's name: {session_data.child_name}")
            if session_data.child_age:
                context_parts.append(f"- Child's age: {session_data.child_age}")
            if session_data.child_gender:
                context_parts.append(f"- Child's gender: {session_data.child_gender}")
            if session_data.challenge_theme:
                context_parts.append(
                    f"- Challenge/theme: {session_data.challenge_theme}"
                )

        if reference_images:
            context_parts.append(
                f"- 📸 Reference images available: {len(reference_images)} image(s)"
            )
            context_parts.append(
                "- Use these images when generating seed images for more personalized results"
            )
            context_parts.append(
                "- ✅ CHILD PHOTOS UPLOADED - Reference images requirement met"
            )

        if seed_status:
            if seed_status["seed_generated"]:
                context_parts.append(
                    "- 🎨 SEED IMAGE GENERATED - Waiting for parent approval"
                )
                if seed_status["seed_approved"]:
                    context_parts.append(
                        "- ✅ SEED IMAGE APPROVED - Ready to create story!"
                    )
                else:
                    context_parts.append(
                        "- ⏳ Ask parent: 'Does this look like [child's name]? Should I proceed?'"
                    )
            elif not missing_fields:
                context_parts.append(
                    "- 🎯 Ready to generate seed image - All info collected!"
                )

        if missing_fields:
            context_parts.append(
                f"- Still need to collect: {', '.join(missing_fields)}"
            )
            if "reference_images" in missing_fields:
                context_parts.append(
                    "- ⚠️ Child's photo is REQUIRED - ask parent to upload at least one clear photo"
                )

        # Final status check
        if not missing_fields and seed_status and seed_status["seed_approved"]:
            context_parts.append(
                "- 🚀 ALL REQUIREMENTS MET - Ready for story generation!"
            )
        elif not missing_fields and not (seed_status and seed_status["seed_generated"]):
            context_parts.append(
                "- 🎨 Generate seed image first, then wait for approval"
            )

        return "\n".join(context_parts)

    async def _extract_and_update_session_data(
        self, session_id: str, user_message: str, ai_response: str
    ) -> None:
        import re

        updates = {}

        if "name" in user_message.lower():
            name_match = re.search(
                r"(?:name is|called|i\'?m)\s+([A-Za-z]+)", user_message, re.IGNORECASE
            )
            if name_match:
                updates["child_name"] = name_match.group(1).capitalize()

        if "old" in user_message.lower() or "age" in user_message.lower():
            age_match = re.search(r"\b([3-8])\b", user_message)
            if age_match:
                updates["child_age"] = int(age_match.group(1))

        gender_words = {
            "boy": "boy",
            "girl": "girl",
            "he": "boy",
            "she": "girl",
            "him": "boy",
            "her": "girl",
        }
        for word, gender in gender_words.items():
            if word in user_message.lower():
                updates["child_gender"] = gender
                break

        if any(
            word in user_message.lower()
            for word in [
                "scared",
                "afraid",
                "shy",
                "angry",
                "sharing",
                "bedtime",
                "potty",
            ]
        ):
            updates["challenge_theme"] = user_message

        # Handle seed approval responses
        approval_words = [
            "yes",
            "looks good",
            "approve",
            "proceed",
            "perfect",
            "that's right",
            "correct",
        ]
        rejection_words = [
            "no",
            "doesn't look",
            "wrong",
            "not right",
            "try again",
            "different",
        ]

        user_lower = user_message.lower()
        if any(word in user_lower for word in approval_words):
            await self.session_manager.approve_seed_image(session_id, True)
        elif any(word in user_lower for word in rejection_words):
            await self.session_manager.approve_seed_image(session_id, False)

        if updates:
            await self.session_manager.update_session_data(session_id, **updates)

    async def create_new_session(self) -> str:
        return await self.session_manager.create_session()
