"""Agent 相关 Pydantic 模型。"""

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """触发 Agent 工作流请求。"""

    user_id: int = Field(description="用户 ID")
    job_id: int = Field(description="目标岗位 ID")


class GapOut(BaseModel):
    """差距项。"""

    gap_type: str
    skill_name: str | None = None
    priority: str
    current_level: int | None = None
    target_level: int | None = None
    current_years: float | None = None
    target_years: int | None = None
    suggested_action: str | None = None


class PlanTaskOut(BaseModel):
    """学习计划任务。"""

    task_name: str
    description: str | None = None
    resource_url: str | None = None
    priority: str = "medium"
    estimated_days: int | None = None


class KnowledgeSourceOut(BaseModel):
    """引用的知识库来源。"""

    doc_title: str
    similarity: float


class AgentReportOut(BaseModel):
    """Agent 最终报告。"""

    success: bool
    position_title: str | None = None
    overall_score: int = 0
    skill_match: int = 0
    experience_match: int = 0
    education_match: int = 0
    analysis: str = ""
    gaps: list[GapOut] = []
    plan: list[PlanTaskOut] = []
    knowledge_sources: list[KnowledgeSourceOut] = []
    errors: list[str] = []


class AgentChatRequest(BaseModel):
    """Agent 对话请求（多轮记忆）。"""

    message: str = Field(min_length=1, max_length=4000, description="用户消息")
    conversation_id: int | None = Field(default=None, description="会话 ID，空则新建")


class AgentChatResponse(BaseModel):
    """Agent 对话响应。"""

    conversation_id: int
    answer: str
    tools_used: int = 0
