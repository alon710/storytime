from typing import Literal
from pathlib import Path
from pydantic import BaseModel


class SeedImageData(BaseModel):
    """Seed image data stored in state"""

    image_path: Path  # Absolute path to temporary file
    prompt_used: str | None = None
    mime_type: Literal["image/png", "image/jpeg"] = "image/png"
    previous_image_paths: list[Path] = []  # All reference images (user-uploaded + previously generated)
    feedback: str | None = None  # Parent's refinement requests
    approved: bool = False
