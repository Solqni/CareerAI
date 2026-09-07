from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import JobAnalysis, JobRequirement, User
from app.schemas.job import JDParsedResult, JobOut, JobParseRequest
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
    await db.refresh(job)
    return job