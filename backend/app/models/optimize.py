from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OptimizeReport(Base):
    """简历优化建议报告（M4）。

    持久化每次生成的优化建议，同一用户同一岗位再次请求时直接返回缓存结果，
    避免重复调用 LLM；传入 refresh=True 可强制重新生成并覆盖展示。
    """

    __tablename__ = "optimize_report"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_analysis.id"), index=True)
    resume_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suggestions_json: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    knowledge_refs_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
