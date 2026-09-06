from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_session"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job_analysis.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    finished_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    qas: Mapped[list["InterviewQA"]] = relationship(back_populates="session")


class InterviewQA(Base):
    __tablename__ = "interview_qa"

    session_id: Mapped[int] = mapped_column(ForeignKey("interview_session.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped["InterviewSession"] = relationship(back_populates="qas")
