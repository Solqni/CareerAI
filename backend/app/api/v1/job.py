from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models import JobAnalysis, JobRequirement, User
from app.schemas.job import JDParsedResult, JobListItem, JobOut, JobParseRequest
from app.services.parsing import parse_jd

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/parse", response_model=JobOut)
async def parse_job_endpoint(
    payload: JobParseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """解析 JD 文本，提取岗位要求。"""
    parsed: JDParsedResult = await parse_jd(payload.jd_text)

    job = JobAnalysis(
        user_id=current_user.id,
        jd_text=payload.jd_text,
        parsed_json=parsed.model_dump(),
    )
    db.add(job)
    await db.flush()

    # 清除旧的需求项并写入新的
    await db.execute(delete(JobRequirement).where(JobRequirement.job_id == job.id))

    for skill in parsed.required_skills:
        if not skill.skill_name:
            continue
        db.add(JobRequirement(
            job_id=job.id,
            skill_name=skill.skill_name,
            requirement_level=skill.requirement_level or "must",
            category=skill.category,
        ))

    await db.commit()
    # 重新查询并预加载 requirements，避免响应序列化时触发懒加载
    job = await db.scalar(
        select(JobAnalysis)
        .where(JobAnalysis.id == job.id)
        .options(selectinload(JobAnalysis.requirements))
    )
    return job


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
    # 先删除关联的需求项，避免 SQLite 外键置空触发 NOT NULL 约束
    await db.execute(delete(JobRequirement).where(JobRequirement.job_id == job.id))
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