from typing import Literal
from pydantic import BaseModel


Style = Literal["photoreal", "watercolor", "comic"]
Gender = Literal["male", "female"]


class ImageRequest(BaseModel):
    seed_image_path: str
    style: Style
    age: int
    gender: Gender


class ImageResult(BaseModel):
    image_path: str
    params_used: dict