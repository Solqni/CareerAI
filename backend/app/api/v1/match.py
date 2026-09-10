from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, Resume, JobAnalysis, MatchReport
from app.schemas.match import MatchCreate, MatchOut, MatchListItem
from app.services.match_analysis import calculate_match_report

router = APIRouter(prefix="/match", tags=["match"])


@router.post("/analyze", response_model=MatchOut)
async def analyze_match(
    payload: MatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """分析简历与岗位的匹配度"""
    # 验证简历是否存在
    resume_result = await db.scalar(
        select(Resume)
        .where(Resume.id == payload.resume_id)
        .where(Resume.user_id == current_user.id)
    )
    if not resume_result:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 验证岗位是否存在
    job_result = await db.scalar(
        select(JobAnalysis)
        .where(JobAnalysis.id == payload.job_id)
        .where(JobAnalysis.user_id == current_user.id)
    )
    if not job_result:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 计算匹配度
    match_report = await calculate_match_report(resume_result, job_result, db)

    # 保存匹配结果
    db.add(match_report)
    await db.commit()
    await db.refresh(match_report)

    return match_report


@router.get("/")
async def list_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取匹配报告列表"""
    result = await db.execute(
        select(MatchReport)
        .where(MatchReport.user_id == current_user.id)
        .order_by(MatchReport.analyzed_at.desc())
        .limit(10)
    )
    return {"user_id": current_user.id, "reports": result.scalars().all()}


@router.get("/{match_id}", response_model=MatchOut)
async def get_match_detail(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取匹配详情"""
    result = await db.scalar(
        select(MatchReport)
        .where(MatchReport.id == match_id)
        .where(MatchReport.user_id == current_user.id)
    )
    if not result:
        raise HTTPException(status_code=404, detail="匹配报告不存在")
    return result
