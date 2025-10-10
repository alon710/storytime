from pydantic import BaseModel


class Page(BaseModel):
    number: int
    title: str
    content: str
    scene_description: str


class BookData(BaseModel):
    pages: list[Page]
    approved: bool = False
