from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from src.nodes.utils import load_prompt

ENV_FILE_PATH = Path(__file__).parent.parent / ".env"


class ChallengeDiscoverySettings(BaseSettings):
    model: str = Field("gpt-4o", alias="CHALLENGE_DISCOVERY_MODEL")
    temperature: float = Field(0.7, alias="CHALLENGE_DISCOVERY_TEMPERATURE")
    system_prompt: str = Field(
        default_factory=lambda: load_prompt("challenge_discovery"),
        alias="CHALLENGE_DISCOVERY_SYSTEM_PROMPT",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


class NarratorSettings(BaseSettings):
    model: str = Field("gpt-4o", alias="NARRATOR_MODEL")
    temperature: float = Field(0.8, alias="NARRATOR_TEMPERATURE")
    max_tokens: int = Field(4096, alias="NARRATOR_MAX_TOKENS")
    system_prompt: str = Field(
        default_factory=lambda: load_prompt("narrator"),
        alias="NARRATOR_SYSTEM_PROMPT",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


class SeedImageSettings(BaseSettings):
    model: str = Field("models/gemini-2.5-flash-image", alias="SEED_IMAGE_MODEL")
    conversational_model: str = Field("gpt-4", alias="SEED_IMAGE_CONVERSATIONAL_MODEL")
    temperature: float = Field(0.7, alias="SEED_IMAGE_TEMPERATURE")
    max_tokens: int = Field(8192, alias="SEED_IMAGE_MAX_TOKENS")
    system_prompt: str = Field(
        default_factory=lambda: load_prompt("seed_image"),
        alias="SEED_IMAGE_SYSTEM_PROMPT",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LangsmithSettings(BaseSettings):
    tracing: bool = Field(False, alias="LANGSMITH_TRACING")
    endpoint: str = Field("https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT")
    api_key: SecretStr | None = Field(None, alias="LANGSMITH_API_KEY")
    project: str = Field("storytime", alias="LANGSMITH_PROJECT")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    openai_api_key: SecretStr = Field(alias="OPENAI_API_KEY")
    google_api_key: SecretStr = Field(alias="GOOGLE_API_KEY")
    challenge_discovery: ChallengeDiscoverySettings = Field(default_factory=ChallengeDiscoverySettings)
    seed_image: SeedImageSettings = Field(default_factory=SeedImageSettings)
    narrator: NarratorSettings = Field(default_factory=NarratorSettings)
    langsmith: LangsmithSettings = Field(default_factory=LangsmithSettings)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
