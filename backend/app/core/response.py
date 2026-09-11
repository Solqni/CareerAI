"""统一 API 响应格式：{"code": 200, "data": ..., "message": "ok"}。"""

from typing import Any


def ok(data: Any = None, message: str = "ok") -> dict:
    """成功响应。"""
    return {"code": 200, "data": data, "message": message}


def fail(message: str, code: int = 400, data: Any = None) -> dict:
    """失败响应（HTTP 状态码仍可为 200，业务码用 code 区分）。"""
    return {"code": code, "data": data, "message": message}
