from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

CURRENT_DIR = Path(__file__).parent


class ConversationalAgentSettings(BaseSettings):
    max_conversation_length: int = Field(10, alias="CONVERSATIONAL_AGENT_MAX_CONVERSATION_LENGTH")
    response_timeout: int = Field(30, alias="CONVERSATIONAL_AGENT_RESPONSE_TIMEOUT")
    temperature: float = Field(0.7, alias="CONVERSATIONAL_AGENT_TEMPERATURE")
    api_key: SecretStr = Field(..., alias="CONVERSATIONAL_AGENT_API_KEY")
    model_name: str = Field("gpt-5", alias="CONVERSATIONAL_AGENT_MODEL_NAME")
    system_prompt: str = Field(
        default="You are a helpful assistant. Always use the available tools when users request specific actions. For images, pictures, or visual content, you MUST use the generate_image tool. Never try to generate images directly."
    )

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AppSettings(BaseSettings):
    name: str = Field(default="Children Stories Chat")
    icon: str = Field(default="👶")
    title: str = Field(default="Chat with a parental consultant")

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ChatSettings(BaseSettings):
    placeholder: str = Field(default="What would you like to ask the parental consultant?")


class ImagesGeneratorToolSettings(BaseSettings):
    api_key: SecretStr = Field(..., alias="IMAGES_GENERATOR_TOOL_API_KEY")
    model_name: str = Field(
        "models/gemini-2.0-flash-preview-image-generation", alias="IMAGES_GENERATOR_TOOL_MODEL_NAME"
    )
    system_prompt: str = Field(
        default="You are an image generation assistant. Generate creative and detailed images based on user prompts."
    )
    tool_description: str = Field(
        default="Generate creative and detailed images based on user prompts. Returns a list of base64-encoded images."
    )
    temperature: float = Field(default=0.7, alias="IMAGES_GENERATOR_TOOL_TEMPERATURE")
    max_output_tokens: int = Field(default=8192, alias="IMAGES_GENERATOR_TOOL_MAX_OUTPUT_TOKENS")

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ToolsSettings(BaseSettings):
    images_generator: ImagesGeneratorToolSettings = Field(default_factory=ImagesGeneratorToolSettings)

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    conversational_agent: ConversationalAgentSettings = Field(default_factory=ConversationalAgentSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    chat: ChatSettings = Field(default_factory=ChatSettings)
    tools: ToolsSettings = Field(default_factory=ToolsSettings)
    is_development_mode: bool = Field(False, alias="IS_DEVELOPMENT_MODE")
    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
