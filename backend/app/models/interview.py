from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InterviewSession(Base):
    """面试会话（需求 4.1 表 11）。"""

    __tablename__ = "interview_session"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_analysis.id"), nullable=True
    )
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resume.id"), nullable=True
    )
    # active（进行中）/ finished（已结束）
    status: Mapped[str] = mapped_column(String(32), default="active")
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 面试结束后的总评报告（LLM 汇总各轮评价）
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    qas: Mapped[list["InterviewQA"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="InterviewQA.id"
    )


class InterviewQA(Base):
    """面试问答记录（需求 4.1 表 12）。"""

    __tablename__ = "interview_qa"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_session.id"), index=True
    )
    # 题型：technical（技术题）/ project（项目题）/ behavioral（行为题）
    category: Mapped[str] = mapped_column(String(32), default="technical")
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 本轮综合得分 0-100
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 文字评估（优点/不足/改进建议的简要文本）
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 多维度评估明细：
    # {"scores": {"logic":..,"completeness":..,"professionalism":..},
    #  "strengths":..,"weaknesses":..,"suggestions":..,"source":"llm|fallback"}
    feedback_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    session: Mapped["InterviewSession"] = relationship(back_populates="qas")
