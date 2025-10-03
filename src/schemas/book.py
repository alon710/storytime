from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class BookPage(BaseModel):
    """Data model for a single page in the children's book.

    Each page contains the story text, scene description for illustration,
    and a reference to the generated illustration.
    """

    page_number: int = Field(..., description="Page number (1-indexed)", ge=1, examples=[1, 2, 3])
    title: str = Field(
        ..., description="Title or heading for this page", min_length=1, examples=["Emma's Bedtime Adventure Begins"]
    )
    story_content: str = Field(
        ...,
        description="Age-appropriate story text for this page (2-4 sentences)",
        min_length=1,
        examples=[
            "Emma loved bedtime stories, but she was afraid of the dark. Every night, she would ask her parents to leave all the lights on."
        ],
    )
    scene_description: str = Field(
        ...,
        description="Detailed visual description for the illustrator (3-5 sentences describing composition, mood, visual elements)",
        min_length=1,
        examples=[
            "A cozy bedroom at twilight with soft purple and blue hues. Emma sits on her bed clutching a teddy bear, looking nervously at the window."
        ],
    )
    illustration_path: Optional[Path] = Field(
        None,
        description="Path to the generated illustration for this page",
        examples=["/tmp/page_1_illustration_abc123.png"],
    )

    @field_validator("illustration_path", mode="before")
    @classmethod
    def convert_str_to_path(cls, v):
        """Convert string paths to Path objects."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        return v



class BookContent(BaseModel):
    """Data model for the complete book content.

    Contains the book title, all pages with their content and scene descriptions,
    and overall style guidance for consistent illustrations.
    """

    book_title: str = Field(
        ..., description="Title of the children's book", min_length=1, examples=["Emma's Brave Night", "Jack's Big Day"]
    )
    pages: list[BookPage] = Field(..., description="All pages in the book", min_length=1)
    total_pages: int = Field(..., description="Total number of pages in the book", ge=1, examples=[8, 10, 12])
    style_guidance: str = Field(
        ...,
        description="Overall artistic style guidance for all illustrations (e.g., watercolor, modern digital, 3D animation)",
        min_length=1,
        examples=[
            "Watercolor illustration style inspired by Beatrix Potter, with warm colors and a magical, dreamlike quality."
        ],
    )

    @field_validator("total_pages")
    @classmethod
    def validate_total_pages(cls, v, info):
        """Ensure total_pages matches the number of pages."""
        if "pages" in info.data and len(info.data["pages"]) != v:
            raise ValueError(f"total_pages ({v}) must match the number of pages ({len(info.data['pages'])})")
        return v

