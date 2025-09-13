from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ArtStyle(str, Enum):
    watercolor = "watercolor"
    cartoon = "cartoon"
    ghibli = "ghibli"
    digital = "digital"
    pixar = "pixar"


class Suffix(str, Enum):
    png = ".png"
    jpg = ".jpg"
    jpeg = ".jpeg"


class PageData(BaseModel):
    title: str
    story_text: str
    illustration_prompt: str


class StoryMetadata(BaseModel):
    """Metadata for story generation."""
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None  # Free-text instructions for AI
    art_style: Optional[ArtStyle] = ArtStyle.watercolor
    additional_context: Optional[str] = None


class StoryTemplate(BaseModel):
    """Story template structure."""
    name: str
    description: str
    default_title: str
    pages: list[PageData]


class GeneratedPage(BaseModel):
    """Generated page with content and image."""
    page_number: int
    title: str
    text: str
    edited_text: Optional[str] = None
    image_path: Optional[str] = None
    illustration_prompt: str