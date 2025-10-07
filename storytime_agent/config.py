from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class DiscoverySettings(BaseSettings):
    model: str = Field("gpt-4", alias="DISCOVERY_MODEL")
    temperature: float = Field(0.7, alias="DISCOVERY_TEMPERATURE")
    system_prompt: str = Field(
        """You are a warm, empathetic parental consultant who helps create personalized therapeutic children's books.

Your role:
- Have a natural conversation with the parent about their child's challenge
- Gather: child's name, age, gender (boy or girl), the challenge, and desired outcome
- Be supportive, ask clarifying questions, make the parent feel heard
- Once you have enough info, extract as JSON:

{
  "child_name": "Emma",
  "child_age": 5,
  "child_gender": "girl",
  "challenge_description": "Afraid of the dark, gets anxious at bedtime",
  "additional_context": "Loves princess stories"
}

Be conversational and warm. Don't rush.""",
        alias="DISCOVERY_SYSTEM_PROMPT",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class SeedImageSettings(BaseSettings):
    model: str = Field("models/gemini-2.5-flash-image", alias="SEED_IMAGE_MODEL")
    temperature: float = Field(0.7, alias="SEED_IMAGE_TEMPERATURE")
    max_tokens: int = Field(8192, alias="SEED_IMAGE_MAX_TOKENS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class Settings(BaseSettings):
    openai_api_key: SecretStr = Field(alias="OPENAI_API_KEY")
    google_api_key: SecretStr = Field(alias="GOOGLE_API_KEY")

    discovery: DiscoverySettings = Field(default_factory=DiscoverySettings)
    seed_image: SeedImageSettings = Field(default_factory=SeedImageSettings)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
