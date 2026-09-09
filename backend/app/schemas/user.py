from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMBase


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6)
    email: EmailStr | None = None
    role: Literal["user", "admin"] = "user"


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMBase):
    id: int
    username: str
    email: str | None = None
    role: str


class TokenWithUser(Token):
    """注册/登录后返回 token + 用户信息。"""
    user: UserOut
