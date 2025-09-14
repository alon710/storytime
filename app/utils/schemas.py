from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SessionStateKeys:
    SEED_IMAGES = "seed_images"
    METADATA = "metadata"
    STORY_TEMPLATE = "story_template"
    EDITED_TEMPLATE = "edited_template"
    GENERATED_PAGES = "generated_pages"
    SYSTEM_PROMPT = "system_prompt"
    CHAR_NAME = "char_name"
    CHAR_AGE = "char_age"
    CHAR_GENDER = "char_gender"
    GENERATED_CHARACTER_REF = "generated_character_ref"
    UPLOADED_REFERENCE = "uploaded_reference"
    ART_STYLE = "art_style"
    SYSTEM_PROMPT_SEED = "system_prompt_seed"


class Gender(str, Enum):
    boy = "Boy"
    girl = "Girl"


class ReferenceMethod(str, Enum):
    upload = "Upload Reference Image"
    generate = "Generate from Photos"


class ArtStyle(str, Enum):
    watercolor = "watercolor"
    cartoon = "cartoon"
    ghibli = "ghibli"
    vintage = "vintage"
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
    instructions: Optional[str] = None
    art_style: Optional[ArtStyle] = ArtStyle.watercolor
    age: int
    gender: str
    character_name: str


class SeedImageData(BaseModel):
    images: list = []
    metadata: Optional[StoryMetadata] = None


class StoryTemplate(BaseModel):
    name: str
    description: str
    default_title: str
    pages: list[PageData]


class GeneratedPage(BaseModel):
    page_number: int
    title: str
    text: str
    edited_text: Optional[str] = None
    image_path: Optional[str] = None
    illustration_prompt: str
