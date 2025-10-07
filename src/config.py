from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ENV_FILE_PATH = Path(__file__).parent.parent / ".env"


class ChallengeDiscoverySettings(BaseSettings):
    model: str = Field("gpt-4", alias="CHALLENGE_DISCOVERY_MODEL")
    temperature: float = Field(0.7, alias="CHALLENGE_DISCOVERY_TEMPERATURE")
    system_prompt: str = Field(
        """You are a warm, empathetic parental consultant who helps create personalized therapeutic children's books.

Your role:
- Have a natural conversation with the parent about their child's challenge
- Gather: child's name, age, gender (boy or girl), the challenge, and desired outcome
- Be supportive, ask clarifying questions, make the parent feel heard
- Once you have enough info, return structured data:

{
  "child": {
    "name": "Emma",
    "age": 5,
    "gender": "girl"
  },
  "challenge_description": "Afraid of the dark, gets anxious at bedtime",
  "additional_context": "Loves princess stories"
}

Be conversational and warm. Don't rush.""",
        alias="CHALLENGE_DISCOVERY_SYSTEM_PROMPT",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


class SeedImageSettings(BaseSettings):
    model: str = Field("models/gemini-2.5-flash-image", alias="SEED_IMAGE_MODEL")
    temperature: float = Field(0.7, alias="SEED_IMAGE_TEMPERATURE")
    max_tokens: int = Field(8192, alias="SEED_IMAGE_MAX_TOKENS")
    system_prompt: str = Field(
        """Create a character reference sheet showing the same {{ gender }} in TWO different poses within a SINGLE image:

LEFT SIDE: Front-facing view (looking directly at camera/viewer)
RIGHT SIDE: Side profile view (facing to the right)

Art style: {{ art_style_description }}
Character Name: {{ character_name }}

REQUIREMENTS:
- Synthesize features from all reference images to create a consistent character design
- Both poses should be consistent - same clothing, hair, and features
- Clear split composition with both poses in the same image
- No text or labels in the image
- Child-friendly, warm, and welcoming style
- Both poses should be full body or at least torso up
- Maintain consistent proportions between both poses
- Apply the specified art style uniformly to both poses
- Clean white or simple background

COMPOSITION:
- Single cohesive image with two character poses
- Left pose: Front view facing forward
- Right pose: Side profile view
- Both poses should be clearly visible and well-proportioned
- Consistent lighting and art style across both poses

IMPORTANT: The character is {{ character_age }} years old. Ensure the character's appearance, proportions, and features clearly reflect a {{ character_age }}-year-old {{ gender }}.

IMAGE SIZE REQUIREMENTS:
- Generate image in SQUARE format (1:1 aspect ratio)
- Target dimensions: 800x800 pixels
- Maintain consistent square size across all generated images""",
        alias="SEED_IMAGE_SYSTEM_PROMPT",
    )

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

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
