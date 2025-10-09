from pydantic import BaseModel

from enum import Enum


class Gender(Enum):
    BOY = "boy"
    GIRL = "girl"


class ChildData(BaseModel):
    name: str
    age: int
    gender: Gender | None = None


class ChallengeData(BaseModel):
    child: ChildData
    challenge_description: str
    additional_context: str | None = None
    approved: bool = False
