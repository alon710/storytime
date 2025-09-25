from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

CURRENT_DIR = Path(__file__).parent


class ConversationalAgentSettings(BaseSettings):
    max_conversation_length: int = Field(10, alias="CONVERSATIONAL_AGENT_MAX_CONVERSATION_LENGTH")
    response_timeout: int = Field(30, alias="CONVERSATIONAL_AGENT_RESPONSE_TIMEOUT")
    temperature: float = Field(0.7, alias="CONVERSATIONAL_AGENT_TEMPERATURE")
    api_key: SecretStr = Field(..., alias="CONVERSATIONAL_AGENT_API_KEY")
    model_name: str = Field("gpt-3.5-turbo", alias="CONVERSATIONAL_AGENT_MODEL_NAME")

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    conversational_agent: ConversationalAgentSettings = Field(default_factory=ConversationalAgentSettings)

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
