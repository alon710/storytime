from pydantic import BaseModel, Field
import google.genai as genai
import asyncio
from app.settings import settings
from app.tools.base import BaseTool, BaseToolResponse
from typing import Type


class StoryPage(BaseModel):
    title: str
    text: str
    scene_description: str


class StoryBook(BaseModel):
    book_title: str
    pages: list[StoryPage]


class NarratorToolResponse(BaseToolResponse):
    story_content: dict | None = Field(None, description="Generated story content")
    pages_count: int = Field(0, description="Number of pages generated")


class NarratorTool(BaseTool):
    name: str = "generate_story"
    description: str = "Creates personalized children's stories with structured pages including titles, text, and scene descriptions for illustrations"
    system_prompt: str = """You are a creative children's book author specializing in personalized storytelling.
Your role is to craft engaging, age-appropriate stories that help children overcome challenges and learn valuable lessons.
Focus on positive messaging, character development, and vivid scene descriptions that translate well to illustrations."""

    def __init__(self):
        super().__init__(
            model=settings.narrator_model,
            name="generate_story",
            description="Creates personalized children's stories with structured pages including titles, text, and scene descriptions for illustrations",
            system_prompt="""You are a creative children's book author specializing in personalized storytelling.
Your role is to craft engaging, age-appropriate stories that help children overcome challenges and learn valuable lessons.
Focus on positive messaging, character development, and vivid scene descriptions that translate well to illustrations.""",
        )

    @property
    def response_model(self) -> Type[NarratorToolResponse]:
        return NarratorToolResponse

    async def _arun(self, **kwargs) -> str:
        try:
            # Handle different argument formats that LangChain might send
            if "args" in kwargs and isinstance(kwargs["args"], list) and kwargs["args"]:
                args = kwargs["args"][0] if kwargs["args"] else {}
                child_name = args.get("name", "child")
                child_age = int(args.get("age", 4))
                child_gender = args.get("gender", "child")
                challenge_theme = args.get("challenge", "learning something new")
            else:
                child_name = kwargs.get("child_name", "child")
                child_age = int(kwargs.get("child_age", 4))
                child_gender = kwargs.get("child_gender", "child")
                challenge_theme = kwargs.get(
                    "challenge_theme", "learning something new"
                )

            result = await self.execute(
                child_name, child_age, child_gender, challenge_theme
            )
            return (
                f"Generated story: {result.book_title}"
                if result
                else "Failed to generate story"
            )
        except Exception as e:
            return f"Error generating story: {str(e)}"

    async def execute(
        self, child_name: str, child_age: int, child_gender: str, challenge_theme: str
    ) -> StoryBook | None:
        self.log_start("story_generation", child_name=child_name, theme=challenge_theme)

        try:
            prompt = self._build_story_prompt(
                child_name, child_age, child_gender, challenge_theme
            )

            from app.settings import settings

            client = genai.Client(api_key=settings.google_api_key)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.model, contents=prompt
                ),
            )

            story_book = self._extract_story_from_response(response)

            if story_book:
                self.log_success(
                    "story_generation",
                    book_title=story_book.book_title,
                    pages_count=len(story_book.pages),
                )
                return story_book
            else:
                self.log_failure(
                    "story_generation", error="Failed to parse story response"
                )
                return None

        except Exception as e:
            self.log_failure("story_generation", error=str(e), child_name=child_name)
            return None

    def _build_story_prompt(self, name: str, age: int, gender: str, theme: str) -> str:
        return f"""Create a personalized children's book for {name}, a {age}-year-old {gender}.

Theme/Challenge: {theme}

Requirements:
- Age-appropriate content for {age} years old
- 6-8 pages of story content
- Each page should have a clear title, engaging text (2-3 sentences), and a detailed scene description for illustration
- The story should help {name} understand or overcome the challenge: {theme}
- Use {name} as the main character
- Include positive messaging and resolution
- Scene descriptions should be vivid and specific for consistent illustration generation

Please respond with a JSON object in this exact format:
{{
  "book_title": "The title of the book",
  "pages": [
    {{
      "title": "Page title",
      "text": "Story text for this page (2-3 sentences)",
      "scene_description": "Detailed description of the scene for illustration purposes"
    }}
  ]
}}"""

    def _extract_story_from_response(self, response) -> StoryBook | None:
        try:
            if hasattr(response, "text"):
                import json

                story_data = json.loads(response.text)
                return StoryBook(**story_data)
            return None
        except Exception:
            return None
