from pydantic_settings import BaseSettings
from pathlib import Path
from pydantic import Field


class Settings(BaseSettings):
    main_agent_model: str = "gpt-4o-mini"
    seed_model: str = "gemini-2.0-flash-exp"
    narrator_model: str = "gemini-1.5-pro"
    illustrator_model: str = "gemini-2.5-flash-image-preview"
    storage_backend: str = "local"

    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    google_api_key: str | None = Field(default=None, env="GOOGLE_API_KEY")

    session_storage_path: str = "./sessions"

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
