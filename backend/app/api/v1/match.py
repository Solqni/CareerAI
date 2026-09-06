from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User

router = APIRouter(prefix="/match", tags=["match"])


@router.get("/")
async def list_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取匹配报告列表（占位）。"""
    return {"user_id": current_user.id, "reports": []}
