from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class GapSeverity(str, Enum):
    """差距严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GapItem(BaseModel):
    """差距项"""
    type: str = Field(..., description="差距类型：skill, experience, education")
    skill_name: Optional[str] = Field(None, description="技能名称")
    current_level: Optional[int] = Field(None, description="当前水平")
    target_level: Optional[int] = Field(None, description="目标水平")
    current_years: Optional[float] = Field(None, description="当前年限")
    target_years: Optional[int] = Field(None, description="目标年限")
    current_education: Optional[str] = Field(None, description="当前学历")
    target_education: Optional[str] = Field(None, description="目标学历")
    experience_type: Optional[str] = Field(None, description="经验类型")
    severity: GapSeverity = Field(GapSeverity.MEDIUM, description="严重程度")
    description: str = Field(..., description="差距描述")


class Recommendation(BaseModel):
    """建议"""
    type: str = Field(..., description="建议类型")
    description: str = Field(..., description="建议描述")
    priority: GapSeverity = Field(GapSeverity.MEDIUM, description="优先级")
    estimated_time: Optional[str] = Field(None, description="预估时间")


class MatchCreate(BaseModel):
    """创建匹配请求"""
    resume_id: int = Field(..., description="简历ID")
    job_id: int = Field(..., description="岗位ID")


class MatchOut(ORMBase):
    """匹配报告输出"""
    id: str
    user_id: int
    job_id: int
    position_title: str
    skill_match: float = Field(..., ge=0, le=100, description="技能匹配度")
    experience_match: float = Field(..., ge=0, le=100, description="经验匹配度")
    education_match: float = Field(..., ge=0, le=100, description="教育匹配度")
    overall_score: float = Field(..., ge=0, le=100, description="综合评分")
    summary: Optional[str] = Field(None, description="LLM 综合分析文字（失败降级为规则文本）")
    detail_json: Optional[dict] = Field(None, description="分析来源与规则摘要等附加数据")
    gaps: List[GapItem] = Field(default_factory=list, description="差距项")
    recommendations: List[Recommendation] = Field(default_factory=list, description="建议")
    learning_plan: List["LearningPlanOut"] = Field(
        default_factory=list, description="学习计划列表（含任务）"
    )
    created_at: datetime
    analyzed_at: datetime


class MatchListItem(BaseModel):
    """匹配报告列表项"""
    id: str
    job_id: int
    position_title: str
    overall_score: float
    skill_match: float
    experience_match: float
    education_match: float
    created_at: datetime
    analyzed_at: datetime


class MatchAnalysisResult(BaseModel):
    """匹配分析结果"""
    match_report: MatchOut
    feedback: str
    learning_plan: List[dict]


class LearningTaskOut(ORMBase):
    """学习任务输出"""
    id: int
    plan_id: int
    task_name: str
    description: Optional[str] = None
    resource_url: Optional[str] = None
    priority: str = "medium"
    estimated_days: Optional[int] = None
    status: str = "todo"
    due_date: Optional[str] = None


class LearningPlanOut(ORMBase):
    """学习计划输出"""
    id: int
    user_id: int
    report_id: str
    content_json: Optional[dict] = None
    status: str = "pending"
    tasks: List[LearningTaskOut] = Field(default_factory=list, description="学习任务列表")


class TaskStatus(str, Enum):
    """学习任务状态（需求 UC-012：待开始/进行中/已完成）"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskStatusUpdate(BaseModel):
    """学习任务状态更新请求"""
    status: TaskStatus = Field(..., description="任务状态：todo / in_progress / done")
