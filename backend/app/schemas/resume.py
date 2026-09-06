from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class ResumeParseRequest(BaseModel):
    raw_text: str


class ResumeOut(ORMBase):
    id: int
    user_id: int
    raw_text: str | None = None
    parsed_json: dict | None = None


class SkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=128)
    proficiency: int = Field(default=3, ge=1, le=5)


class SkillOut(ORMBase):
    id: int
    skill_name: str
    proficiency: int
    source: str


class ProfileOut(BaseModel):
    """能力画像：基本信息 + 技能 + 经历。"""

    username: str
    email: str | None = None
    phone: str | None = None
    education: str | None = None
    skills: list[SkillOut] = []
    experiences: list[str] = []
    summary: str | None = None
