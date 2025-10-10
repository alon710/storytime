from typing import Literal
from pydantic import BaseModel


class SeedImageData(BaseModel):
    """Seed image data stored in state"""

    image_path: str  # Absolute path to temporary file
    prompt_used: str | None = None
    mime_type: Literal["image/png", "image/jpeg"] = "image/png"
    approved: bool = False
