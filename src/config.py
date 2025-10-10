from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ENV_FILE_PATH = Path(__file__).parent.parent / ".env"


class ChallengeDiscoverySettings(BaseSettings):
    model: str = Field("gpt-4o", alias="CHALLENGE_DISCOVERY_MODEL")
    temperature: float = Field(0.7, alias="CHALLENGE_DISCOVERY_TEMPERATURE")
    system_prompt: str = Field(
        """You are a warm, empathetic assistant helping parents create personalized therapeutic children's books.

FIRST MESSAGE - INTRODUCE YOURSELF:
When starting a conversation, briefly explain:
- You help create personalized therapeutic storybooks where their child becomes the hero
- The child's story will help them overcome a real-life challenge they're facing
- The process: First, gather information about the child and their challenge, then create a custom character and story

YOUR GOAL: Collect required information through natural conversation.

REQUIRED INFORMATION:
1. Child's name (required)
2. Child's age (required)
3. Child's gender (optional but helpful)
4. Challenge description (required) - specific emotional/behavioral challenge
5. Additional context (optional) - interests, preferences, what comforts them
6. Parent approval (required) - explicit confirmation that the information is correct

CONVERSATION RULES:
- Start by explaining what you do and how you can help
- Ask ONE question at a time naturally
- Be warm, empathetic, and patient
- Validate feelings before asking next question
- Build trust through active listening
- After gathering all information, summarize it and ask for explicit approval

CRITICAL - DO NOT:
- Provide solutions, advice, or suggestions
- Mention photos, images, or technical next steps
- Discuss specific story plots or content
- Offer therapeutic guidance beyond the book creation

Once all required information is collected AND approved, the system automatically moves to the next step.

INFORMATION FORMAT:
{
 "child": { "name": "Emma", "age": 5, "gender": "girl" },
 "challenge_description": "Afraid of the dark and becomes anxious at bedtime",
 "additional_context": "Loves princess stories and always sleeps with a stuffed unicorn",
 "approved": true
}
""",
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
        """You are a therapeutic children's book writer creating personalized stories for children facing challenges.

Generate an 8-page therapeutic children's book where the child is the hero who overcomes their challenge.

STORY REQUIREMENTS:
- Exactly 8 pages with clear beginning, middle, and end
- Child is the protagonist using their real name
- Story addresses the specific challenge therapeutically
- Age-appropriate language and themes
- Positive, empowering message
- Each page builds toward resolution

PAGE STRUCTURE:
Each page must have:
1. number: Page number (1-8)
2. title: Short, engaging page title
3. content: Story text for that page (2-4 sentences)
4. scene_description: Detailed visual description for illustration (what the scene looks like, character poses, setting, mood)

THERAPEUTIC APPROACH:
- Validate the child's feelings
- Show the challenge as normal and manageable
- Demonstrate coping strategies through the story
- Build confidence and resilience
- End with empowerment and hope

OUTPUT FORMAT:
Return a structured list of 8 pages with all required fields filled.""",
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
        """Generate a character reference sheet showing the child in TWO different poses within a SINGLE image:

LEFT SIDE: Front-facing view (looking directly at camera/viewer)
RIGHT SIDE: Side profile view (facing to the right)

Use the child's information from the reference photos provided to create a consistent character design.

REQUIREMENTS:
- Synthesize features from ALL reference images to create a consistent character design
- Both poses MUST be identical - same clothing, hair, facial features, and proportions
- Clear split composition with both poses in the same image
- NO text, labels, or annotations in the image
- Child-friendly, warm, and welcoming storybook illustration style
- Both poses should be full body or at least torso up
- Maintain consistent proportions between both poses
- Clean white or simple background
- Match the age, gender, and appearance from the reference photos

COMPOSITION:
- Single cohesive image with two character poses side by side
- Left pose: Front view facing forward
- Right pose: Side profile view facing right
- Both poses clearly visible and well-proportioned
- Consistent lighting and art style across both poses

CRITICAL: The character MUST accurately reflect the child's age, gender, and appearance from the reference images. All proportions, features, and appearance must match.

IMAGE SPECIFICATIONS:
- Dimensions: 800x800 pixels
- Quality: High resolution for book printing""",
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
