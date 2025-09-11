"""
Configuration settings using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Google/Gemini API Configuration - accepts either variable name
    google_api_key: str
    
    # Model Configuration  
    model: str = "gemini-2.5-flash-image-preview"
    
    # Generation Settings
    max_pages: int = 15
    
    # Rate Limiting Settings
    retry_on_quota_error: bool = True
    delay_between_images: int = 5  # seconds
    max_retries: int = 3
    base_retry_delay: int = 60  # seconds for exponential backoff
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()