from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """密码 bcrypt 哈希。"""
    # 直接使用bcrypt避免passlib兼容性问题
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """直接使用bcrypt验证密码"""
    try:
        # 直接使用bcrypt验证
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except:
        # 如果失败，尝试passlib的方式
        try:
            return pwd_context.verify(plain, hashed)
        except:
            return False


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """生成 JWT access token。"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
