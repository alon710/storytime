from pydantic import BaseModel


class SeedImageData(BaseModel):
    image_path: str
    prompt_used: str | None = None
    approved: bool = False
