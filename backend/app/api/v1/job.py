from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models import JobAnalysis, JobRequirement, User
from app.schemas.job import JobListItem, JobOut, JobParseRequest
from app.services.parsing import parse_jd as rule_parse_jd

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/parse", response_model=JobOut)
async def parse_job(
    payload: JobParseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """解析 JD 文本，提取岗位要求并入库。"""
    if not payload.jd_text.strip():
        raise HTTPException(status_code=400, detail="JD 内容为空")

    parsed = rule_parse_jd(payload.jd_text)
    job = JobAnalysis(
        user_id=current_user.id,
        jd_text=payload.jd_text,
        parsed_json={"title": parsed["title"], "summary": parsed["summary"]},
    )
    db.add(job)
    await db.flush()

    for req in parsed["requirements"]:
        db.add(
            JobRequirement(
                job_id=job.id,
                skill_name=req["skill_name"],
                requirement_level=req["requirement_level"],
                category=req["category"],
            )
        )
    await db.commit()
    return await _get_job_or_404(job.id, current_user, db)


@router.get("", response_model=list[JobListItem])
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """岗位知识库：当前用户的岗位分析列表。"""
    result = await db.scalars(
        select(JobAnalysis)
        .where(JobAnalysis.user_id == current_user.id)
        .options(selectinload(JobAnalysis.requirements))
        .order_by(JobAnalysis.id.desc())
    )
    return [
        JobListItem(
            id=job.id,
            parsed_json=job.parsed_json,
            created_at=job.created_at,
            requirement_count=len(job.requirements),
        )
        for job in result.all()
    ]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """岗位知识库：查看单条岗位分析详情。"""
    return await _get_job_or_404(job_id, current_user, db)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """岗位知识库：删除一条岗位分析记录。"""
    job = await _get_job_or_404(job_id, current_user, db)
    await db.delete(job)
    await db.commit()


async def _get_job_or_404(
    job_id: int, current_user: User, db: AsyncSession
) -> JobAnalysis:
    job = await db.scalar(
        select(JobAnalysis)
        .where(JobAnalysis.id == job_id, JobAnalysis.user_id == current_user.id)
        .options(selectinload(JobAnalysis.requirements))
    )
    if not job:
        raise HTTPException(status_code=404, detail="岗位分析记录不存在")
    return job
