"""job_analyzer Tool：获取岗位分析结果与岗位要求（真实连接 DB）。"""

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import async_session
from app.models import JobAnalysis


async def analyze_job_impl(db: AsyncSession, job_id: int) -> dict:
    """读取指定岗位的解析结果与要求明细。"""
    job = await db.scalar(
        select(JobAnalysis)
        .where(JobAnalysis.id == job_id)
        .options(selectinload(JobAnalysis.requirements))
    )
    if not job:
        return {"found": False, "message": f"岗位 {job_id} 不存在"}

    parsed = job.parsed_json or {}
    return {
        "found": True,
        "job_id": job.id,
        "position_title": parsed.get("position_title", "未命名岗位"),
        "summary": parsed.get("summary"),
        "responsibilities": parsed.get("responsibilities", []),
        "requirements": [
            {
                "skill_name": r.skill_name,
                "requirement_level": r.requirement_level,
                "category": r.category,
            }
            for r in job.requirements
        ],
        "education": parsed.get("education"),
        "experience_requirement": parsed.get("experience_requirement"),
    }


@tool
async def job_analyzer(job_id: int) -> dict:
    """获取指定岗位分析的完整信息，包括岗位名称、职责、技能要求（必备/加分）与学历经验要求。"""
    async with async_session() as db:
        return await analyze_job_impl(db, job_id)
