from datetime import datetime

from pydantic import BaseModel, Field

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


# ===== LLM 结构化输出 =====

class ParsedJobRequirement(BaseModel):
    skill_name: str | None = Field(default=None, description="技能名称")
    requirement_level: str | None = Field(default="must", description="要求级别: must / plus")
    category: str | None = Field(default=None, description="分类: 技术 / 工具 / 领域 / 软技能")


class JDParsedResult(BaseModel):
    """LLM JD 解析结构化输出"""
    position_title: str | None = Field(default=None, description="岗位名称")
    responsibilities: list[str] = Field(default_factory=list, description="岗位职责")
    required_skills: list[ParsedJobRequirement] = Field(default_factory=list, description="技能要求")
    education_requirement: str | None = Field(default=None, description="学历要求")
    experience_requirement: str | None = Field(default=None, description="经验要求")
    summary: str | None = Field(default=None, description="岗位概述")