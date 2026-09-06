from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import JobAnalysis, User
from app.schemas.job import JobOut, JobParseRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/parse", response_model=JobOut)
async def parse_job(
    payload: JobParseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """JD 解析（占位，后续接入 LLM 工具 parse_jd）。"""
    job = JobAnalysis(user_id=current_user.id, jd_text=payload.jd_text)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job
