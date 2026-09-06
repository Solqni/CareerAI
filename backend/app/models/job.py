from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class JobAnalysis(Base):
    __tablename__ = "job_analysis"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    jd_text: Mapped[str] = mapped_column(Text)
    parsed_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    requirements: Mapped[list["JobRequirement"]] = relationship(back_populates="job")


class JobRequirement(Base):
    __tablename__ = "job_requirement"

    job_id: Mapped[int] = mapped_column(ForeignKey("job_analysis.id"), index=True)
    skill_name: Mapped[str] = mapped_column(String(128))
    requirement_level: Mapped[str] = mapped_column(String(32))
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)

    job: Mapped["JobAnalysis"] = relationship(back_populates="requirements")
