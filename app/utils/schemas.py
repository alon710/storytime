from enum import Enum
from pydantic import BaseModel


class ArtStyle(str, Enum):
    watercolor = "watercolor"
    cartoon = "cartoon"
    ghibli = "ghibli"
    digital = "digital"
    pixar = "pixar"


class Gender(str, Enum):
    boy = "boy"
    girl = "girl"


class Suffix(str, Enum):
    png = ".png"
    jpg = ".jpg"
    jpeg = ".jpeg"
    ttf = ".ttf"
    pdf = ".pdf"


class PageData(BaseModel):
    title: str
    story_text: str
    illustration_prompt: str


class PersonalizedPage(BaseModel):
    page_number: int
    title: str
    personalized_text: str


class PersonalizedStoryBook(BaseModel):
    personalized_pages: list[PersonalizedPage]


class Colors(str, Enum):
    PRIMARY = "#2C3E50"  # Soft charcoal for main text
    SECONDARY = "#E79771F5"  # Soft peach for text backgrounds
    ACCENT = "#E8BBCA"  # Playful pink for page numbers
    OVERLAY = "#00000066"  # 40% black for text background overlays
    TEXT_LIGHT = "#FFFFFF"  # White for text on dark backgrounds
