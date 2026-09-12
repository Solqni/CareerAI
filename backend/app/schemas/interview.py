"""面试准备模块（M5，需求 3.5）Pydantic 模型。

- 面试题生成：技术题 / 项目题 / 行为题三类
- 模拟面试：会话 + 多轮问答
- 答案评估：逻辑性 / 完整性 / 专业性三维度评分 + 优点/不足/改进建议
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class InterviewCategory(str, Enum):
    """面试题类型（需求 3.5：技术题、项目题、行为题）"""

    TECHNICAL = "technical"  # 技术题
    PROJECT = "project"  # 项目题
    BEHAVIORAL = "behavioral"  # 行为题


class InterviewCreate(BaseModel):
    """创建模拟面试会话请求"""

    job_id: int = Field(..., description="目标岗位ID（已解析的 job_analysis）")
    resume_id: Optional[int] = Field(None, description="简历ID，缺省取用户最新简历")
    question_count: int = Field(6, ge=3, le=9, description="题目数量（3-9，三类尽量均匀）")


class QuestionGenerateRequest(BaseModel):
    """仅生成面试题（不开面试会话）请求"""

    job_id: int = Field(..., description="目标岗位ID")
    resume_id: Optional[int] = Field(None, description="简历ID，缺省取用户最新简历")
    question_count: int = Field(6, ge=3, le=9)


class GeneratedQuestion(BaseModel):
    """LLM 生成的单道面试题（结构化输出校验，需求 8.3）"""

    category: InterviewCategory
    question: str = Field(..., min_length=2)


class QAOut(ORMBase):
    """单轮问答记录输出"""

    id: int
    session_id: int
    category: str
    question: str
    answer: Optional[str] = None
    score: Optional[int] = Field(None, description="本轮综合得分 0-100")
    feedback: Optional[str] = None
    feedback_json: Optional[dict] = Field(
        None, description="三维度评分与优点/不足/建议明细"
    )


class SessionOut(BaseModel):
    """面试会话详情输出（含全部问答）"""

    id: int
    user_id: int
    job_id: Optional[int] = None
    resume_id: Optional[int] = None
    position_title: Optional[str] = None
    status: str
    summary: Optional[str] = Field(None, description="面试结束后的总评报告")
    created_at: datetime
    finished_at: Optional[datetime] = None
    qas: List[QAOut] = Field(default_factory=list)


class SessionListItem(BaseModel):
    """面试会话列表项"""

    id: int
    job_id: Optional[int] = None
    position_title: Optional[str] = None
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None
    qa_count: int
    answered_count: int
    average_score: Optional[float] = None


class AnswerSubmit(BaseModel):
    """提交一轮回答"""

    qa_id: int = Field(..., description="本轮问答记录ID")
    answer: str = Field(..., min_length=1, description="用户回答文本")


class AnswerResult(BaseModel):
    """提交回答后的返回：本轮评估 + 下一道待答题"""

    qa: QAOut
    next_qa: Optional[QAOut] = None
    is_finished: bool = Field(..., description="是否已无待答题（可结束面试生成总评）")


class QuestionBankResponse(BaseModel):
    """面试题生成结果"""

    job_id: int
    position_title: Optional[str] = None
    questions: List[GeneratedQuestion] = Field(default_factory=list)
    source: str = Field("llm", description="题目来源：llm / fallback")
