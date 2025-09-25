from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(dotenv_path=Path(".env"))


class ConversationalAgentSettings(BaseSettings):
    max_conversation_length: int = Field(10, alias="CONVERSATIONAL_AGENT_MAX_CONVERSATION_LENGTH")
    response_timeout: int = Field(30, alias="CONVERSATIONAL_AGENT_RESPONSE_TIMEOUT")
    temperature: float = Field(0.7, alias="CONVERSATIONAL_AGENT_TEMPERATURE")
    api_key: SecretStr = Field(default=..., alias="CONVERSATIONAL_AGENT_API_KEY")
    model_name: str = Field("gpt-3.5-turbo", alias="CONVERSATIONAL_AGENT_MODEL_NAME")


class Settings(BaseSettings):
    conversational_agent: ConversationalAgentSettings = ConversationalAgentSettings()

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
