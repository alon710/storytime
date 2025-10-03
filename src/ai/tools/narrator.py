from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from typing import Optional
import json

from core.settings import settings
from core.session import session_context
from core.workflow_state import workflow_state_manager
from core.logger import logger
from schemas.challenge import ChallengeData
from schemas.book import BookContent, BookPage
from schemas.common import ToolResponse


@tool(description=settings.tools.narrator.tool_description)
def generate_book_content(
    challenge_data_json: str,  # JSON string of ChallengeData
    num_pages: int = 8,
    style_preference: Optional[str] = None,
) -> dict:
    """Generate complete book content based on the child's challenge.

    Creates a therapeutic children's book with title, pages, and illustration guidance.
    Each page follows a narrative arc helping the child overcome their challenge.

    Args:
        challenge_data_json: JSON string containing ChallengeData
        num_pages: Number of pages in the book (default 8)
        style_preference: Optional style (e.g., "rhyming", "adventure", "gentle")

    Returns:
        dict: Serialized ToolResponse[BookContent] with book content or error
    """
    session_id = session_context.get_current_session()

    logger.info(
        "Book narration started",
        session_id=session_id,
        num_pages=num_pages,
        has_style_preference=bool(style_preference),
    )

    try:
        # Parse challenge data from JSON
        challenge_dict = json.loads(challenge_data_json)
        challenge_data = ChallengeData(**challenge_dict)

        # Validate num_pages
        if num_pages < 4 or num_pages > 20:
            error_msg = f"num_pages must be between 4 and 20, got {num_pages}"
            logger.error("Book narration validation failed", error=error_msg, session_id=session_id)
            return ToolResponse[BookContent](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        # Build system prompt for book generation
        system_prompt = f"""You are an expert children's book author specializing in therapeutic storytelling.

Your task is to create a {num_pages}-page children's book where {challenge_data.child_name} (age {challenge_data.child_age}) is the hero who overcomes the challenge of: {challenge_data.challenge_type}.

Challenge details: {challenge_data.details}
Desired outcome: {challenge_data.desired_outcome}

NARRATIVE REQUIREMENTS:
1. {challenge_data.child_name} must be the main character and hero of the story
2. Follow this narrative arc across {num_pages} pages:
   - Pages 1-2: Introduction - show {challenge_data.child_name}'s normal world and hint at the challenge
   - Pages 3-4: Challenge appears - the difficulty becomes clear and feels overwhelming
   - Pages 5-6: Hero struggles and tries different approaches - show resilience
   - Pages 7-{num_pages-1}: Hero overcomes - {challenge_data.child_name} succeeds using courage/creativity
   - Page {num_pages}: Resolution - celebrate success and reinforce the lesson learned

CONTENT REQUIREMENTS FOR EACH PAGE:
1. Title: Short, engaging page heading (3-7 words)
2. Story content: Age-appropriate text (2-4 sentences per page) that:
   - Uses simple language for a {challenge_data.child_age}-year-old
   - Shows emotions and validates feelings
   - Demonstrates positive coping strategies
   - Builds confidence and hope
3. Scene description: Detailed visual guide for the illustrator (3-5 sentences) including:
   - Setting and environment details
   - Character positioning and expression
   - Mood and lighting
   - Key visual elements that support the story
   - Composition suggestions

STYLE REQUIREMENTS:
- Tone: {style_preference if style_preference else "warm, encouraging, and age-appropriate"}
- Language: Simple, clear, engaging for age {challenge_data.child_age}
- Therapeutic: Normalize the challenge, show it can be overcome, build self-efficacy
- Positive: Emphasize {challenge_data.child_name}'s strengths and growth

ILLUSTRATION STYLE GUIDANCE:
Choose ONE consistent artistic style for all illustrations. Examples:
- "Watercolor with soft edges, warm colors, and dreamlike quality"
- "Modern digital illustration with bold colors and clean lines"
- "Soft painted style with gentle textures and pastel palette"

OUTPUT FORMAT (JSON):
{{
  "book_title": "A creative, uplifting title featuring {challenge_data.child_name}'s name",
  "style_guidance": "Detailed description of the consistent artistic style for all illustrations",
  "pages": [
    {{
      "page_number": 1,
      "title": "Page heading",
      "story_content": "The story text for this page (2-4 sentences).",
      "scene_description": "Detailed visual description for the illustrator. Include setting, character positioning, mood, lighting, and key visual elements."
    }},
    ... (continue for all {num_pages} pages)
  ]
}}

Remember: This book should help {challenge_data.child_name} feel brave, capable, and hopeful about overcoming {challenge_data.challenge_type}."""

        # Generate book content
        narrator_llm = ChatOpenAI(
            openai_api_key=settings.tools.narrator.api_key.get_secret_value(),  # type: ignore
            model_name=settings.tools.narrator.model_name,
            temperature=settings.tools.narrator.temperature,
            max_tokens=settings.tools.narrator.max_output_tokens,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate the complete {num_pages}-page book for {challenge_data.child_name}. Return ONLY valid JSON matching the specified format."),
        ]

        response = narrator_llm.invoke(messages)

        # Extract text content
        if isinstance(response.content, str):
            response_text = response.content.strip()
        else:
            error_msg = "Unexpected response content type from LLM"
            logger.error("Book narration unexpected response", session_id=session_id)
            return ToolResponse[BookContent](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        # Parse JSON response
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

        book_data = json.loads(response_text)

        # Convert to BookContent model
        pages_list = [BookPage(**page) for page in book_data["pages"]]

        book_content = BookContent(
            book_title=book_data["book_title"],
            pages=pages_list,
            total_pages=len(pages_list),
            style_guidance=book_data["style_guidance"],
        )

        # Validate book content
        if len(book_content.pages) != num_pages:
            error_msg = f"Generated {len(book_content.pages)} pages but expected {num_pages}"
            logger.error("Book narration validation failed", error=error_msg, session_id=session_id)
            return ToolResponse[BookContent](
                success=False,
                data=None,
                error_message=error_msg,
                metadata={"session_id": session_id},
            ).model_dump()

        # Verify child's name appears in the story
        full_text = book_content.book_title + " " + " ".join(page.story_content for page in book_content.pages)
        if challenge_data.child_name.lower() not in full_text.lower():
            logger.warning(
                "Child's name not found in generated book",
                child_name=challenge_data.child_name,
                session_id=session_id,
            )

        # Update workflow state
        if session_id:
            workflow_state_manager.update_workflow_state(
                session_id=session_id,
                book_content=book_content,
            )
            logger.info(
                "Workflow state updated with book content",
                session_id=session_id,
                book_title=book_content.book_title,
                total_pages=book_content.total_pages,
            )
        else:
            logger.warning("No session_id available, skipping workflow state update")

        # Return success response
        response_data = ToolResponse[BookContent](
            success=True,
            data=book_content,
            error_message=None,
            metadata={
                "session_id": session_id,
                "book_title": book_content.book_title,
                "total_pages": book_content.total_pages,
                "child_name": challenge_data.child_name,
                "step_completed": "narration",
            },
        )

        logger.info("Book narration completed successfully", session_id=session_id, book_title=book_content.book_title)
        return response_data.model_dump()

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse book content JSON: {str(e)}"
        logger.error(
            "Book narration JSON parsing error",
            error=str(e),
            session_id=session_id,
        )
        return ToolResponse[BookContent](
            success=False,
            data=None,
            error_message=error_msg,
            metadata={"session_id": session_id, "error_type": "JSONDecodeError"},
        ).model_dump()

    except Exception as e:
        error_msg = f"Book narration failed: {str(e)}"
        logger.error(
            "Book narration error",
            error=str(e),
            error_type=type(e).__name__,
            session_id=session_id,
        )
        return ToolResponse[BookContent](
            success=False,
            data=None,
            error_message=error_msg,
            metadata={"session_id": session_id, "error_type": type(e).__name__},
        ).model_dump()
