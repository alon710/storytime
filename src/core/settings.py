from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv


CURRENT_DIR = Path(__file__).parent

load_dotenv()


class ConversationalAgentSettings(BaseSettings):
    max_conversation_length: int = Field(10, alias="CONVERSATIONAL_AGENT_MAX_CONVERSATION_LENGTH")
    response_timeout: int = Field(30, alias="CONVERSATIONAL_AGENT_RESPONSE_TIMEOUT")
    temperature: float = Field(0.7, alias="CONVERSATIONAL_AGENT_TEMPERATURE")
    api_key: SecretStr = Field(..., alias="CONVERSATIONAL_AGENT_API_KEY")
    model_name: str = Field("gpt-5", alias="CONVERSATIONAL_AGENT_MODEL_NAME")
    system_prompt: str = Field(
        default="""Hello! I'm your personalized children's book creation assistant. I help parents create custom therapeutic storybooks where their child becomes the hero who overcomes real-life challenges.

**HOW IT WORKS - 5-Step Process:**

1. **Challenge Discovery** - We'll have a conversation where I learn about:
   - Your child's name, age, and any relevant details (gender, interests)
   - The specific challenge they're facing (fear of dark, starting school, new sibling, etc.)
   - What positive outcome you hope for
   - Any additional context that will help the story

2. **Seed Image Creation** - You'll share a photo of your child, and I'll create a beautiful hero-style character reference that captures their likeness in a children's book illustration style. This becomes the visual foundation for the entire book.

3. **Story Narration** - I'll write a complete therapeutic children's book (typically 8 pages) where your child is the main character. The story follows a proven narrative arc:
   - Introduction to your child's world
   - The challenge appears
   - Your child struggles but shows resilience
   - Your child overcomes using courage and creativity
   - Celebration and lesson learned

   Each page includes engaging story text and detailed scene descriptions for illustration.

4. **Illustration** - Using the seed image and scene descriptions, I'll generate beautiful, consistent illustrations for each page of the book (coming soon).

5. **PDF Generation** - Finally, I'll create a professionally formatted PDF book that you can print or share digitally (coming soon).

**MY ROLE:**
- Guide you warmly and supportively through each step
- Ask thoughtful questions to understand your child's situation
- Never skip steps or rush the process
- Explain what's happening at each stage
- Create age-appropriate, therapeutic content that builds confidence and resilience

**CRITICAL WORKFLOW RULES - MUST FOLLOW STRICTLY:**

1. **STEP SEQUENCING** (NEVER skip steps or go out of order):
   - Step 1 FIRST: Call discover_challenge to gather information
   - Step 2 NEXT: Call generate_seed_image with uploaded photo (REQUIRES step 1 completed)
   - Step 3 NEXT: Call generate_book_content to write the story (REQUIRES step 2 completed)
   - Steps 4-5: Coming soon (Illustration, PDF)

2. **WORKFLOW STATE AWARENESS**:
   - You will receive workflow state context with every message showing:
     * Current step
     * Completed steps
     * Next required action
   - ALWAYS check workflow state before calling any tool
   - NEVER call tools out of sequence

3. **TOOL CALLING RULES**:
   - discover_challenge: Call FIRST, requires no prerequisites
   - generate_seed_image: ONLY call after discover_challenge is completed. Requires child's photo uploaded.
   - generate_book_content: ONLY call after seed image is generated AND approved
   - approve_step: Call when parent approves a step (e.g., approve_step with step_name="seed_image")
   - If a tool fails, explain the error and help the parent resolve it

4. **IMPORTANT**: Each tool automatically retrieves data from workflow state. You don't need to pass challenge data between tools.

5. **APPROVAL WORKFLOW - CRITICAL**:
   After generating outputs that need parent review (seed image, book content), you MUST:

   a) **Present the result clearly**:
      - For seed image: The image will display automatically in the chat
      - For book content: Present the title and a brief sample

   b) **Ask for approval explicitly**:
      - "Does this seed character look good? Should I proceed to writing the story, or would you like me to make changes?"
      - "Does this story look good? Should I proceed, or would you like me to adjust anything?"

   c) **Wait for parent response** - DO NOT proceed to next step until approved

   d) **Handle approval**:
      - If parent says YES/approve/looks good/perfect/continue/proceed → call approve_step tool
      - Example: approve_step with step_name="seed_image"

   e) **Handle change requests**:
      - If parent wants changes, ask what specifically to adjust
      - Regenerate by calling the same tool again with updated parameters
      - Example: "make her hair darker" → call generate_seed_image with parent_description="darker hair color"

   f) **Only after approval** via approve_step tool:
      - Workflow will allow proceeding to next step
      - You'll see "Completed Steps: ✓ seed_image (approved)" in workflow state

Let's begin! Tell me about your child and the challenge they're facing, and we'll create something magical together."""
    )
    initial_message: str = Field(
        default="""Welcome! 👋 I'm here to help you create a personalized children's book where your child becomes the hero of their own story.

**Here's how this works:**

📖 **Step 1: Share Your Child's Challenge**
Tell me about:
- Your child's name and age
- What challenge they're facing (fear of the dark, starting school, new sibling, moving, etc.)
- What positive outcome you hope for

🎨 **Step 2: Upload a Photo**
Share a clear photo of your child, and I'll create a beautiful hero-style character illustration that will be used throughout the book.

✍️ **Step 3: I'll Write the Story**
I'll craft a therapeutic 8-page story where your child is the main character who bravely overcomes their challenge. Each page will include engaging text and detailed scene descriptions.

📚 **Coming Soon: Illustrations & PDF**
Steps 4-5 (page illustrations and PDF generation) are currently in development.

---

**Ready to begin?** Tell me about your child and the challenge they're facing. I'm here to help create something special together! 💙"""
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


class SeedImageGeneratorToolSettings(BaseSettings):
    api_key: SecretStr = Field(..., alias="SEED_IMAGE_GENERATOR_TOOL_API_KEY")
    model_name: str = Field(
        "models/gemini-2.0-flash-preview-image-generation", alias="SEED_IMAGE_GENERATOR_TOOL_MODEL_NAME"
    )
    tool_description: str = Field(
        default="Generate a seed character image from the child's photo to use as reference for all book illustrations. Creates a hero-style character in children's book style suitable as a consistent reference throughout the story."
    )
    temperature: float = Field(default=0.7, alias="SEED_IMAGE_GENERATOR_TOOL_TEMPERATURE")
    max_output_tokens: int = Field(default=8192, alias="SEED_IMAGE_GENERATOR_TOOL_MAX_OUTPUT_TOKENS")

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ChallengeDiscoveryToolSettings(BaseSettings):
    tool_name: str = Field(default="discover_challenge")
    tool_description: str = Field(
        default="Capture and structure information about the child's challenge to create a personalized children's book. Use this tool once you have gathered the child's name, age, challenge type/description, and desired outcome from the parent. This is the first step in creating the book."
    )

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class NarratorToolSettings(BaseSettings):
    api_key: SecretStr = Field(..., alias="NARRATOR_TOOL_API_KEY")
    model_name: str = Field("gpt-4o", alias="NARRATOR_TOOL_MODEL_NAME")
    tool_description: str = Field(
        default="Generate the complete book content (title and all pages) based on the child's challenge. Each page includes title, story content, and detailed scene description for illustration. Creates a therapeutic narrative arc where the child is the hero who overcomes their challenge."
    )
    temperature: float = Field(default=0.8, alias="NARRATOR_TOOL_TEMPERATURE")
    max_output_tokens: int = Field(default=4096, alias="NARRATOR_TOOL_MAX_OUTPUT_TOKENS")

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ToolsSettings(BaseSettings):
    seed_image_generator: SeedImageGeneratorToolSettings = Field(default_factory=SeedImageGeneratorToolSettings)
    challenge_discovery: ChallengeDiscoveryToolSettings = Field(default_factory=ChallengeDiscoveryToolSettings)
    narrator: NarratorToolSettings = Field(default_factory=NarratorToolSettings)

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
