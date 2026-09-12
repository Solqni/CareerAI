from typing import Literal, Optional

from pydantic import BaseModel, Field


class AdminRoleUpdate(BaseModel):
    role: Literal["user", "admin"]


class AdminUserUpdate(BaseModel):
    """管理员修改用户信息（全部字段可选，仅提交的字段生效）。"""

    username: Optional[str] = Field(None, min_length=3, max_length=64)
    email: Optional[str] = Field(None, max_length=128)
    role: Optional[Literal["user", "admin"]] = None
    password: Optional[str] = Field(None, min_length=6, max_length=64)


class AICollectJobsRequest(BaseModel):
    """AI 从招聘网站采集岗位请求。"""

    keyword: str = Field(..., min_length=1, max_length=64, description="岗位关键词，如 Python")
    count: int = Field(3, ge=1, le=10, description="采集条数 1-10")


class AICollectKnowledgeRequest(BaseModel):
    """AI 采集知识文档请求。"""

    topic: str = Field(..., min_length=2, max_length=64, description="知识主题，如 后端面试高频考点")
    doc_count: int = Field(1, ge=1, le=3, description="生成文档篇数 1-3")
