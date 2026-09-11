from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MatchReport(Base):
    __tablename__ = "match_report"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_analysis.id"), index=True)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    gaps: Mapped[list["GapItem"]] = relationship(back_populates="report")
    plan: Mapped["LearningPlan | None"] = relationship(back_populates="report")


class GapItem(Base):
    __tablename__ = "gap_item"

    report_id: Mapped[int] = mapped_column(ForeignKey("match_report.id"), index=True)
    gap_type: Mapped[str] = mapped_column(String(32))
    skill_name: Mapped[str] = mapped_column(String(128))
    priority: Mapped[str] = mapped_column(String(16))
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    report: Mapped["MatchReport"] = relationship(back_populates="gaps")


class LearningPlan(Base):
    __tablename__ = "learning_plan"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("match_report.id"), index=True)
    content_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")

    report: Mapped["MatchReport"] = relationship(back_populates="plan")
    tasks: Mapped[list["LearningTask"]] = relationship(back_populates="plan")


class LearningTask(Base):
    __tablename__ = "learning_task"

    plan_id: Mapped[int] = mapped_column(ForeignKey("learning_plan.id"), index=True)
    task_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="todo")
    due_date: Mapped[str | None] = mapped_column(String(32), nullable=True)

    plan: Mapped["LearningPlan"] = relationship(back_populates="tasks")
