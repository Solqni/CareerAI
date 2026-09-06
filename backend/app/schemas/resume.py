from pydantic import BaseModel

from app.schemas.common import ORMBase


class ResumeParseRequest(BaseModel):
    raw_text: str


class ResumeOut(ORMBase):
    id: int
    user_id: int
    raw_text: str | None = None
    parsed_json: dict | None = None
