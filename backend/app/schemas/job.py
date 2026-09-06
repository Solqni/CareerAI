from pydantic import BaseModel

from app.schemas.common import ORMBase


class JobParseRequest(BaseModel):
    jd_text: str


class JobOut(ORMBase):
    id: int
    user_id: int
    jd_text: str
    parsed_json: dict | None = None
