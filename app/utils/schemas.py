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


class Colors(str, Enum):
    BANNER = "#E8F4FD"
    BACKGROUND = "#FFF8E7"
    ACCENT = "#FFE4E1"
    DARK = "#2E4057"
