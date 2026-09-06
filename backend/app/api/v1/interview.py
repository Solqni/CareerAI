from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/session")
async def create_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建面试会话（占位）。"""
    return {"user_id": current_user.id, "status": "created"}
