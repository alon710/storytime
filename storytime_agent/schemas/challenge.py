from pydantic import BaseModel


class ChallengeData(BaseModel):
    child_name: str
    child_age: int
    child_gender: str
    challenge_description: str
    additional_context: str | None = None
