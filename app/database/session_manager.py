import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
import structlog

from app.database.models import Base, Session, SessionData, ChatHistory, GeneratedContent

logger = structlog.get_logger()


class SessionManager:
    def __init__(self, database_url: str = "sqlite+aiosqlite:///storytime.db"):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
        self.logger = logger.bind(component="session_manager")

    async def initialize(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.info("Database initialized")

    async def create_session(self) -> str:
        session_id = str(uuid.uuid4())

        async with self.async_session() as db:
            db_session = Session(session_id=session_id)
            db_session_data = SessionData(session_id=session_id)

            db.add(db_session)
            db.add(db_session_data)
            await db.commit()

        self.logger.info("Created new session", session_id=session_id)
        return session_id

    async def get_session_data(self, session_id: str) -> SessionData | None:
        async with self.async_session() as db:
            result = await db.execute(
                select(SessionData).where(SessionData.session_id == session_id)
            )
            return result.scalar_one_or_none()

    async def update_session_data(
        self,
        session_id: str,
        child_name: str | None = None,
        child_age: int | None = None,
        child_gender: str | None = None,
        challenge_theme: str | None = None
    ) -> None:
        async with self.async_session() as db:
            result = await db.execute(
                select(SessionData).where(SessionData.session_id == session_id)
            )
            session_data = result.scalar_one_or_none()

            if session_data:
                if child_name is not None:
                    session_data.child_name = child_name
                    session_data.collected_fields["child_name"] = True
                if child_age is not None:
                    session_data.child_age = child_age
                    session_data.collected_fields["child_age"] = True
                if child_gender is not None:
                    session_data.child_gender = child_gender
                    session_data.collected_fields["child_gender"] = True
                if challenge_theme is not None:
                    session_data.challenge_theme = challenge_theme
                    session_data.collected_fields["challenge_theme"] = True

                session_data.is_complete = all([
                    session_data.child_name,
                    session_data.child_age,
                    session_data.child_gender,
                    session_data.challenge_theme
                ])

                await db.commit()
                self.logger.info("Updated session data", session_id=session_id, is_complete=session_data.is_complete)

    async def add_chat_message(self, session_id: str, role: str, content: str) -> None:
        async with self.async_session() as db:
            message = ChatHistory(
                session_id=session_id,
                role=role,
                content=content
            )
            db.add(message)
            await db.commit()

    async def get_chat_history(self, session_id: str, limit: int = 50) -> list[ChatHistory]:
        async with self.async_session() as db:
            result = await db.execute(
                select(ChatHistory)
                .where(ChatHistory.session_id == session_id)
                .order_by(ChatHistory.timestamp.desc())
                .limit(limit)
            )
            messages = result.scalars().all()
            return list(reversed(messages))

    async def save_generated_content(
        self,
        session_id: str,
        story_json: dict,
        image_paths: list[str],
        session_directory: str
    ) -> None:
        async with self.async_session() as db:
            content = GeneratedContent(
                session_id=session_id,
                story_json=story_json,
                image_paths=image_paths,
                session_directory=session_directory
            )
            db.add(content)
            await db.commit()
            self.logger.info("Saved generated content", session_id=session_id)

    async def get_missing_fields(self, session_id: str) -> list[str]:
        session_data = await self.get_session_data(session_id)
        if not session_data:
            return ["child_name", "child_age", "child_gender", "challenge_theme"]

        missing = []
        if not session_data.child_name:
            missing.append("child_name")
        if not session_data.child_age:
            missing.append("child_age")
        if not session_data.child_gender:
            missing.append("child_gender")
        if not session_data.challenge_theme:
            missing.append("challenge_theme")

        return missing