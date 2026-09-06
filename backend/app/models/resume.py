from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserSkill(Base):
    __tablename__ = "user_skill"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    skill_name: Mapped[str] = mapped_column(String(128))
    proficiency: Mapped[int] = mapped_column(Integer, default=3)
    source: Mapped[str] = mapped_column(String(32), default="manual")

    user: Mapped["User"] = relationship(back_populates="skills")


class UserExperience(Base):
    __tablename__ = "user_experience"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_range: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship(back_populates="experiences")
