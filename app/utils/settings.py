from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")

    # Model configurations for different AI tasks
    seed_image_model: str = Field(
        default="gemini-2.0-flash-exp",
        env="SEED_IMAGE_MODEL",
        description="Model used for generating character reference images from photos"
    )
    story_text_model: str = Field(
        default="gemini-2.0-flash-exp",
        env="STORY_TEXT_MODEL",
        description="Model used for text personalization and story processing"
    )
    story_image_model: str = Field(
        default="gemini-2.5-flash-image-preview",
        env="STORY_IMAGE_MODEL",
        description="Model used for generating story illustrations"
    )
    default_model: str = Field(
        default="gemini-2.5-flash-image-preview",
        env="DEFAULT_MODEL",
        description="Fallback model for backward compatibility"
    )

    # Legacy model field for backward compatibility
    model: str = Field(
        default="gemini-2.5-flash-image-preview",
        env="MODEL",
        description="Legacy model field - use specific model fields instead"
    )

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
