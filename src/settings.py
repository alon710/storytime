from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


CURRENT_DIR = Path(__file__).parent

load_dotenv(dotenv_path=CURRENT_DIR.parent / ".env")


class Settings(BaseSettings):
    openai_api_key: str = Field(default=..., alias="OPENAI_API_KEY", description="OpenAI API key for image generation")

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=[CURRENT_DIR.parent / ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
