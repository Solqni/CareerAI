import base64

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models import JobAnalysis, JobRequirement, User
from app.schemas.job import JDParsedResult, JobListItem, JobOut, JobParseRequest
from app.services.parsing import extract_jd_text_from_image, parse_jd
from app.services.admin_ops import delete_job_cascade

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/parse", response_model=JobOut)
async def parse_job_endpoint(
    payload: JobParseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """解析 JD 文本，提取岗位要求并入库。"""
    if not payload.jd_text.strip():
        raise HTTPException(status_code=400, detail="JD 内容为空")

    return await _parse_and_save_job(current_user, payload.jd_text, db)


@router.post("/parse-image", response_model=JobOut)
async def parse_job_image_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传 JD 截图，视觉模型识别文字后解析入库。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    allowed_exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    name = file.filename.lower()
    if not name.endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="仅支持 JPG / PNG / WebP / BMP 图片格式")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="图片内容为空")

    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    ext = "." + name.rsplit(".", 1)[-1]
    data_url = (
        f"data:{mime_map[ext]};base64," + base64.b64encode(file_bytes).decode("ascii")
    )

    try:
        jd_text = await extract_jd_text_from_image(data_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="图片识别服务调用失败，请稍后重试")

    return await _parse_and_save_job(current_user, jd_text, db)


async def _parse_and_save_job(
    current_user: User, jd_text: str, db: AsyncSession
) -> JobAnalysis:
    """核心解析逻辑：调用 LLM 解析 JD → 存储结果与技能要求。"""
    parsed: JDParsedResult = await parse_jd(jd_text)

    job = JobAnalysis(
        user_id=current_user.id,
        jd_text=jd_text,
        parsed_json=parsed.model_dump(),
    )
    db.add(job)
    await db.flush()

    # 清除旧的需求项并写入新的
    await db.execute(delete(JobRequirement).where(JobRequirement.job_id == job.id))

    for skill in parsed.required_skills:
        db.add(JobRequirement(
            job_id=job.id,
            skill_name=skill.skill_name,
            requirement_level=skill.requirement_level,
            category=skill.category,
        ))

    await db.commit()
    # commit 后关系已过期，重新预加载 requirements（避免序列化时懒加载触发 MissingGreenlet）
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
    """岗位知识库：当前用户的岗位 + 管理员共享岗位（AI 采集）。"""
    result = await db.scalars(
        select(JobAnalysis)
        .where(
            or_(
                JobAnalysis.user_id == current_user.id,
                JobAnalysis.is_shared.is_(True),
            )
        )
        .options(selectinload(JobAnalysis.requirements))
        .order_by(JobAnalysis.id.desc())
    )
    return [
        JobListItem(
            id=job.id,
            position_title=(job.parsed_json or {}).get("position_title") or None,
            parsed_json=job.parsed_json,
            created_at=job.created_at,
            requirement_count=len(job.requirements),
            is_shared=job.is_shared,
            is_owner=job.user_id == current_user.id,
        )
        for job in result.all()
    ]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """岗位知识库：查看单条岗位分析详情（自有或平台共享）。"""
    return await _get_job_or_404(job_id, current_user, db, allow_shared=True)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """岗位知识库：删除本人一条岗位分析记录（级联清理其报告/学习计划链，解除面试会话引用）。"""
    job = await _get_job_or_404(job_id, current_user, db)
    await delete_job_cascade(db, [job.id])
    await db.commit()


async def _get_job_or_404(
    job_id: int,
    current_user: User,
    db: AsyncSession,
    allow_shared: bool = False,
) -> JobAnalysis:
    """按 id 取岗位，仅限自有岗位；allow_shared 时放行平台共享岗位（只读场景）。"""
    conditions = [JobAnalysis.id == job_id]
    if allow_shared:
        conditions.append(
            or_(
                JobAnalysis.user_id == current_user.id,
                JobAnalysis.is_shared.is_(True),
            )
        )
    else:
        conditions.append(JobAnalysis.user_id == current_user.id)
    job = await db.scalar(
        select(JobAnalysis)
        .where(*conditions)
        .options(selectinload(JobAnalysis.requirements))
    )
    if not job:
        raise HTTPException(status_code=404, detail="岗位分析记录不存在")
    return job
