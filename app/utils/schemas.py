from pydantic import BaseModel
from enum import Enum


class ArtStyle(str, Enum):
    watercolor = "watercolor"
    cartoon = "cartoon"
    ghibli = "ghibli"
    digital = "digital"
    pixar = "pixar"


class Gender(str, Enum):
    boy = "boy"
    girl = "girl"
