from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import Resume, User
from app.schemas.resume import ResumeOut, ResumeParseRequest

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/parse", response_model=ResumeOut)
async def parse_resume(
    payload: ResumeParseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """简历解析（占位，后续接入 LLM 工具 parse_resume）。"""
    resume = Resume(user_id=current_user.id, raw_text=payload.raw_text)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume
