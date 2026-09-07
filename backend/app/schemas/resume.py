from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMBase


class ResumeParseRequest(BaseModel):
    raw_text: str


class ResumeOut(ORMBase):
    id: int
    user_id: int
    raw_text: str | None = None
    parsed_json: dict | None = None


# ===== LLM 结构化输出 =====

class ParsedSkill(BaseModel):
    skill_name: str | None = Field(default=None, description="技能名称")
    proficiency: int = Field(default=3, ge=1, le=5, description="熟练度 1-5")

    @field_validator("proficiency", mode="before")
    @classmethod
    def coerce_proficiency(cls, v):
        if v is None:
            return 3
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 3
        return v


class ParsedExperience(BaseModel):
    type: str | None = Field(default=None, description="经历类型: work / internship / project")
    title: str | None = Field(default=None, description="职位或项目名称")
    description: str | None = Field(default=None, description="经历描述")
    date_range: str | None = Field(default=None, description="时间范围")


class ParsedEducation(BaseModel):
    school: str | None = Field(default=None, description="学校名称")
    degree: str | None = Field(default=None, description="学历")
    major: str | None = Field(default=None, description="专业")
    date_range: str | None = Field(default=None, description="就读时间")


class ResumeParsedResult(BaseModel):
    """LLM 简历解析结构化输出"""
    name: str | None = Field(default=None, description="姓名")
    email: str | None = Field(default=None, description="邮箱")
    phone: str | None = Field(default=None, description="电话")
    education: list[ParsedEducation] = Field(default_factory=list)
    skills: list[ParsedSkill] = Field(default_factory=list)
    experiences: list[ParsedExperience] = Field(default_factory=list)
    summary: str | None = Field(default=None, description="个人概述")


# ===== 技能 / 能力画像 CRUD =====

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
