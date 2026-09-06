from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import Resume, User, UserSkill
from app.schemas.resume import (
    ProfileOut,
    ResumeOut,
    ResumeParseRequest,
    SkillCreate,
    SkillOut,
)
from app.services.file_extract import extract_text
from app.services.parsing import parse_resume as rule_parse_resume

router = APIRouter(prefix="/resume", tags=["resume"])


async def _save_and_sync_skills(
    db: AsyncSession, user: User, raw_text: str
) -> Resume:
    """解析简历、落库，并把识别到的技能同步到用户技能表。"""
    parsed = rule_parse_resume(raw_text)
    resume = Resume(user_id=user.id, raw_text=raw_text, parsed_json=parsed)
    db.add(resume)

    # 同步技能（已存在的不重复插入）
    existing = set(await db.scalars(select(UserSkill.skill_name).where(UserSkill.user_id == user.id)))
    for skill in parsed["skills"]:
        if skill not in existing:
            db.add(UserSkill(user_id=user.id, skill_name=skill, proficiency=3, source="resume"))

    await db.commit()
    await db.refresh(resume)
    return resume


@router.post("/parse", response_model=ResumeOut)
async def parse_resume_text(
    payload: ResumeParseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """解析粘贴的简历文本。"""
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="简历内容为空")
    return await _save_and_sync_skills(db, current_user, payload.raw_text)


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传简历文件（txt/md/pdf/docx）并解析。"""
    text = await extract_text(file)
    return await _save_and_sync_skills(db, current_user, text)


@router.get("/latest", response_model=ResumeOut)
async def get_latest_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户最近一次解析的简历。"""
    resume = await db.scalar(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc())
        .limit(1)
    )
    if not resume:
        raise HTTPException(status_code=404, detail="暂无简历记录")
    return resume


@router.get("/skills", response_model=list[SkillOut])
async def list_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """技能列表（含简历自动识别 + 手动添加）。"""
    result = await db.scalars(
        select(UserSkill).where(UserSkill.user_id == current_user.id).order_by(UserSkill.id)
    )
    return result.all()


@router.post("/skills", response_model=SkillOut, status_code=201)
async def add_skill(
    payload: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动添加技能。"""
    exists = await db.scalar(
        select(UserSkill).where(
            UserSkill.user_id == current_user.id,
            UserSkill.skill_name == payload.skill_name,
        )
    )
    if exists:
        raise HTTPException(status_code=400, detail="该技能已存在")
    skill = UserSkill(
        user_id=current_user.id,
        skill_name=payload.skill_name,
        proficiency=payload.proficiency,
        source="manual",
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除技能。"""
    skill = await db.get(UserSkill, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="技能不存在")
    await db.delete(skill)
    await db.commit()


@router.get("/profile", response_model=ProfileOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """能力画像：最新简历解析结果 + 技能表合并。"""
    skills = (await db.scalars(
        select(UserSkill).where(UserSkill.user_id == current_user.id).order_by(UserSkill.id)
    )).all()
    resume = await db.scalar(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc())
        .limit(1)
    )
    parsed = resume.parsed_json if resume else None
    return ProfileOut(
        username=current_user.username,
        email=(parsed or {}).get("email") or current_user.email,
        phone=(parsed or {}).get("phone"),
        education=(parsed or {}).get("education"),
        skills=skills,
        experiences=(parsed or {}).get("experiences", []),
        summary=(parsed or {}).get("summary") or "暂无简历数据，请先上传或解析简历",
    )
