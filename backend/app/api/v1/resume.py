from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import Resume, User, UserExperience, UserSkill
from app.schemas.resume import (
    ProfileOut,
    ResumeOut,
    ResumeParseRequest,
    ResumeParsedResult,
    SkillCreate,
    SkillOut,
)
from app.services.file_extract import extract_text
from app.services.parsing import parse_resume

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/parse", response_model=ResumeOut)
async def parse_resume_text(
    payload: ResumeParseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """粘贴简历文本进行 AI 解析。"""
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="简历内容为空")
    return await _do_parse_resume(current_user, payload.raw_text, db)


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传 PDF/Word 简历文件进行 AI 解析。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    allowed_exts = {".pdf", ".docx", ".doc", ".md", ".txt"}
    suffix = file.filename.lower()
    if not any(suffix.endswith(ext) for ext in allowed_exts):
        raise HTTPException(status_code=400, detail="仅支持 PDF / Word / Markdown / TXT 格式")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    try:
        raw_text = extract_text(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="无法从文件中提取文本内容")

    return await _do_parse_resume(current_user, raw_text, db)


async def _do_parse_resume(
    current_user: User,
    raw_text: str,
    db: AsyncSession,
) -> Resume:
    """核心解析逻辑：调用 LLM → 存储结果。"""
    parsed: ResumeParsedResult = await parse_resume(raw_text)

    resume = Resume(
        user_id=current_user.id,
        raw_text=raw_text,
        parsed_json=parsed.model_dump(),
    )
    db.add(resume)
    await db.flush()

    # 清除用户旧数据并写入新解析的技能
    await db.execute(delete(UserSkill).where(UserSkill.user_id == current_user.id))
    await db.execute(delete(UserExperience).where(UserExperience.user_id == current_user.id))

    for skill in parsed.skills:
        if not skill.skill_name:
            continue
        db.add(UserSkill(
            user_id=current_user.id,
            skill_name=skill.skill_name,
            proficiency=skill.proficiency,
            source="resume_parse",
        ))

    for exp in parsed.experiences:
        db.add(UserExperience(
            user_id=current_user.id,
            type=exp.type or "work",
            title=exp.title or "未命名",
            description=exp.description,
            date_range=exp.date_range,
        ))

    await db.commit()
    await db.refresh(resume)
    return resume


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

    # LLM 解析的 education 是 list[dict]（学校/学历/专业），这里拼成字符串以匹配 ProfileOut.education: str
    education_str = None
    edu_raw = (parsed or {}).get("education")
    if edu_raw:
        if isinstance(edu_raw, list) and edu_raw and isinstance(edu_raw[0], dict):
            parts = [
                " ".join(filter(None, [e.get("degree"), e.get("major")]))
                for e in edu_raw
                if e.get("degree") or e.get("major")
            ]
            education_str = " / ".join(parts) if parts else None
        elif isinstance(edu_raw, str):
            education_str = edu_raw

    # LLM 解析的 experiences 是 list[dict]（含 type/title/description/date_range），这里转成字符串列表
    exp_list: list[str] = []
    exp_raw = (parsed or {}).get("experiences", [])
    if exp_raw:
        if exp_raw and isinstance(exp_raw[0], dict):
            for e in exp_raw:
                title = e.get("title") or ""
                desc = e.get("description") or ""
                exp_list.append(f"{title}：{desc}".strip("："))
        else:
            exp_list = list(exp_raw)

    return ProfileOut(
        username=current_user.username,
        email=(parsed or {}).get("email") or current_user.email,
        phone=(parsed or {}).get("phone"),
        education=education_str,
        skills=skills,
        experiences=exp_list,
        summary=(parsed or {}).get("summary") or "暂无简历数据，请先上传或解析简历",
    )
