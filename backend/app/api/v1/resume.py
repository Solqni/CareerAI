from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import Resume, User, UserExperience, UserSkill
from app.schemas.resume import ResumeOut, ResumeParseRequest, ResumeParsedResult
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
    return await _do_parse_resume(current_user, payload.raw_text, db)


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile,
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