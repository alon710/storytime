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
        default="Hello! I'm your friendly parental consultant, here to help with all your parenting questions and needs. I love creating magical children's book illustrations for families!\n\nWhen you share photos with me, I'll automatically create beautiful children's book style character reference sheets showing your child in two poses - front view and side view. I use various artistic styles like watercolor, retro mid-century, modern digital, and 3D animation to bring your child's story to life.\n\nI'm here to chat naturally about parenting, answer your questions, and help create wonderful visual memories. Just upload a photo and I'll get to work creating something special, or ask me anything about parenting - I'm here to help!\n\nFor image generation, I'll use sensible defaults (children's book style, square format, warm colors) unless you specifically ask for something different. No need to specify technical details - I've got that covered!"
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
        default="Create a beautiful children's book style character reference sheet with the child in TWO poses in a SINGLE image: LEFT SIDE shows them facing forward, RIGHT SIDE shows their side profile.\n\nUse a warm, children's book illustration style - choose from watercolor (like Beatrix Potter), retro mid-century (Mary Blair style), modern digital illustration, cinematic 3D animation, or paper cut-out style. The illustration should faithfully preserve the child's facial features, hairstyle, clothing, and proportions, ensuring consistency between both poses.\n\nKey requirements:\n- Both poses show the same child with consistent features, clothing, and proportions\n- Child-friendly, warm, magical atmosphere\n- Clean, simple background for clarity\n- Square format (800x800 pixels)\n- Age-appropriate proportions and features\n- No text or labels in the image\n- Soft, welcoming colors and lighting\n\nThe result should feel like it belongs in a beloved children's storybook!"
    )
    tool_description: str = Field(
        default="Generate children's book style character reference sheets with two poses (front and side view) in various artistic styles including retro mid-century, modern digital, watercolor, 3D animation, paper cut-out, and classic storybook illustrations. Returns a list of base64-encoded images in 800x800 square format."
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
