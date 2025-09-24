from pydantic import BaseModel


class NeedsApproval(BaseModel):
    image_path: str
    params_used: dict


class Finalized(BaseModel):
    message: str