from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    model: str = Field(default="gemini-2.5-flash-image-preview", env="MODEL")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
