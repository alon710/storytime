from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default="active")


class SessionData(Base):
    __tablename__ = "session_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    child_name: Mapped[str | None] = mapped_column(String(100))
    child_age: Mapped[int | None] = mapped_column(Integer)
    child_gender: Mapped[str | None] = mapped_column(String(20))
    challenge_theme: Mapped[str | None] = mapped_column(Text)
    collected_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    is_complete: Mapped[bool] = mapped_column(default=False)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class GeneratedContent(Base):
    __tablename__ = "generated_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    story_json: Mapped[dict | None] = mapped_column(JSON)
    image_paths: Mapped[list | None] = mapped_column(JSON)
    session_directory: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))