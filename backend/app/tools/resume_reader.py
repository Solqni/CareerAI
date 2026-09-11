"""resume_reader Tool：读取用户简历结构化数据（真实连接 DB）。"""

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models import Resume, UserExperience, UserSkill


async def read_resume_impl(db: AsyncSession, user_id: int) -> dict:
    """读取用户最新一次解析的简历、技能与经历。"""
    resume = await db.scalar(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.id.desc()).limit(1)
    )
    skills = list(
        await db.scalars(select(UserSkill).where(UserSkill.user_id == user_id))
    )
    experiences = list(
        await db.scalars(select(UserExperience).where(UserExperience.user_id == user_id))
    )

    if not resume:
        return {"found": False, "message": "用户尚未上传/解析过简历"}

    return {
        "found": True,
        "resume_id": resume.id,
        "parsed_json": resume.parsed_json or {},
        "skills": [
            {"skill_name": s.skill_name, "proficiency": s.proficiency, "source": s.source}
            for s in skills
        ],
        "experiences": [
            {
                "type": e.type,
                "title": e.title,
                "description": e.description,
                "date_range": e.date_range,
            }
            for e in experiences
        ],
    }


@tool
async def resume_reader(user_id: int) -> dict:
    """读取指定用户的简历结构化数据，包括基本信息、技能列表（含熟练度）与经历列表。"""
    async with async_session() as db:
        return await read_resume_impl(db, user_id)
