from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class JobParseRequest(BaseModel):
    jd_text: str


class JobRequirementOut(ORMBase):
    id: int
    skill_name: str
    requirement_level: str
    category: str | None = None


class JobOut(ORMBase):
    id: int
    user_id: int
    jd_text: str
    parsed_json: dict | None = None
    requirements: list[JobRequirementOut] = []


class JobListItem(ORMBase):
    """岗位知识库列表项（不含 JD 全文）。"""

    id: int
    parsed_json: dict | None = None
    created_at: datetime
    requirement_count: int = 0
