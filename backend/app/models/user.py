from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Role(str):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String(16), default=Role.USER)

    skills: Mapped[list["UserSkill"]] = relationship(back_populates="user")
    experiences: Mapped[list["UserExperience"]] = relationship(back_populates="user")
