from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """知识库文档列表（占位，后续接入 RAG）。"""
    return {"documents": []}
