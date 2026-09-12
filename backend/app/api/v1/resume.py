from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import InterviewSession, Resume, User, UserExperience, UserSkill
from app.schemas.resume import (
    ProfileOut,
    ProfileUpdate,
    ResumeListItem,
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


@router.get("/list", response_model=list[ResumeListItem])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """当前用户的简历列表（用于匹配/优化场景的简历选择下拉）。"""
    result = await db.scalars(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.id.desc())
    )
    return [
        ResumeListItem(
            id=r.id,
            name=(r.parsed_json or {}).get("name") or None,
            created_at=r.created_at,
        )
        for r in result.all()
    ]


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


async def _get_latest_resume(db: AsyncSession, user_id: int) -> Resume | None:
    return await db.scalar(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.id.desc())
        .limit(1)
    )


async def _build_profile(current_user: User, db: AsyncSession) -> ProfileOut:
    """能力画像构建：最新简历解析结果 + 技能表合并（GET /profile 与更新后复用）。"""
    skills = (await db.scalars(
        select(UserSkill).where(UserSkill.user_id == current_user.id).order_by(UserSkill.id)
    )).all()
    resume = await _get_latest_resume(db, current_user.id)
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
        parsed_json=parsed,
    )


@router.get("/profile", response_model=ProfileOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """能力画像：最新简历解析结果 + 技能表合并。"""
    return await _build_profile(current_user, db)


@router.put("/profile", response_model=ProfileOut)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新最新简历的基本信息（姓名/邮箱/电话/个人概述），写入 parsed_json。"""
    resume = await _get_latest_resume(db, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="暂无简历记录，请先上传或解析简历")

    parsed = dict(resume.parsed_json or {})
    for key in ("name", "email", "phone", "summary"):
        value = getattr(payload, key)
        if value is not None:
            parsed[key] = value
    resume.parsed_json = parsed
    await db.commit()
    await db.refresh(resume)
    return await _build_profile(current_user, db)


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除本人指定简历；关联的面试会话仅解除引用（resume_id 置空），会话保留。"""
    resume = await db.scalar(
        select(Resume)
        .where(Resume.id == resume_id)
        .where(Resume.user_id == current_user.id)
    )
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    # 先解除面试会话引用，避免外键约束冲突
    await db.execute(
        update(InterviewSession)
        .where(InterviewSession.resume_id == resume_id)
        .values(resume_id=None)
    )
    await db.delete(resume)
    await db.commit()
    return Response(status_code=204)
