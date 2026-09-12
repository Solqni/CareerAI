from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.core.response import fail, ok
from app.core.security import hash_password
from app.models import JobAnalysis, KnowledgeDocument, MatchReport, User
from app.schemas.admin import (
    AICollectJobsRequest,
    AdminUserUpdate,
    AICollectKnowledgeRequest,
)
from app.schemas.user import UserOut
from app.services import admin_ops
from app.services import job_collector
from app.services import knowledge_collector

router = APIRouter(prefix="/admin", tags=["admin"])

_SOURCE_LABELS = {
    "web_ncss": "实时采集",
    "ai_fallback": "AI 模拟",
}


@router.get("/users")
async def list_users(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """用户列表（管理员专属）。"""
    users = await db.scalars(select(User).order_by(User.id))
    return ok([UserOut.model_validate(u).model_dump() for u in users])


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """修改用户信息：用户名/邮箱/角色/密码（仅提交字段生效，管理员专属）。"""
    target = await db.get(User, user_id)
    if not target:
        return fail("用户不存在", code=404)

    fields = payload.model_dump(exclude_unset=True)

    new_username = fields.get("username")
    if new_username is not None:
        new_username = new_username.strip()
        if len(new_username) < 3:
            return fail("用户名至少 3 个字符", code=400)
        dup = await db.scalar(
            select(User).where(User.username == new_username, User.id != user_id)
        )
        if dup:
            return fail(f"用户名「{new_username}」已被占用", code=400)
        target.username = new_username

    if "email" in fields:
        email = fields["email"]
        email = (email or "").strip() or None
        if email:
            dup = await db.scalar(
                select(User).where(User.email == email, User.id != user_id)
            )
            if dup:
                return fail(f"邮箱「{email}」已被占用", code=400)
        target.email = email

    new_role = fields.get("role")
    if new_role is not None and new_role != target.role:
        if target.role == "admin" and new_role != "admin":
            if await admin_ops.count_admins(db) <= 1:
                return fail("系统至少需要保留一名管理员，无法降级", code=400)
        target.role = new_role

    new_password = fields.get("password")
    if new_password:
        target.password_hash = hash_password(new_password)

    await db.commit()
    await db.refresh(target)
    return ok(UserOut.model_validate(target).model_dump(), message="用户信息已更新")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除用户及其全部业务数据（简历/岗位/报告/面试/对话，管理员专属）。"""
    target = await db.get(User, user_id)
    if not target:
        return fail("用户不存在", code=404)
    if target.id == current_user.id:
        return fail("不能删除当前登录的管理员账号", code=400)
    if target.role == "admin" and await admin_ops.count_admins(db) <= 1:
        return fail("系统至少需要保留一名管理员，无法删除", code=400)

    await admin_ops.delete_user_cascade(db, user_id)
    await db.commit()
    return ok(message=f"用户「{target.username}」及其全部数据已删除")


@router.get("/system")
async def system_info(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """系统统计数据（管理员专属）。"""
    user_count = await db.scalar(select(func.count(User.id)))
    job_count = await db.scalar(select(func.count(JobAnalysis.id)))
    report_count = await db.scalar(select(func.count(MatchReport.id)))
    doc_count = await db.scalar(select(func.count(KnowledgeDocument.id)))
    return ok(
        {
            "user_count": user_count,
            "job_count": job_count,
            "match_report_count": report_count,
            "knowledge_doc_count": doc_count,
        }
    )


@router.get("/jobs")
async def list_all_jobs(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """全平台岗位列表（含归属与来源，管理员专属）。"""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(JobAnalysis, User.username)
        .join(User, JobAnalysis.user_id == User.id)
        .options(selectinload(JobAnalysis.requirements))
        .order_by(JobAnalysis.id.desc())
        .limit(200)
    )
    items = []
    for job, owner in result.all():
        parsed = job.parsed_json or {}
        source = parsed.get("source") or "manual"
        items.append(
            {
                "id": job.id,
                "position_title": parsed.get("position_title"),
                "company": parsed.get("company"),
                "city": parsed.get("city"),
                "source": source,
                "source_label": _SOURCE_LABELS.get(source, "手动录入"),
                "is_shared": bool(job.is_shared),
                "owner_username": owner,
                "requirement_count": len(job.requirements),
                "created_at": job.created_at,
            }
        )
    return ok(items)


@router.delete("/jobs/{job_id}")
async def delete_any_job(
    job_id: int,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除任意岗位及其关联报告（管理员专属）。"""
    job = await db.get(JobAnalysis, job_id)
    if not job:
        return fail("岗位不存在", code=404)
    await admin_ops.delete_job_cascade(db, [job_id])
    await db.commit()
    return ok(message=f"岗位 #{job_id} 及其关联数据已删除")


@router.post("/jobs/ai-collect")
async def ai_collect_jobs(
    payload: AICollectJobsRequest,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """AI 从招聘网站采集岗位：真实爬取国家大学生就业服务平台，失败降级 LLM 模拟。

    采集结果为全平台共享岗位，所有用户的能力匹配均可选用。
    """
    try:
        result = await job_collector.collect_jobs_from_web(
            db, current_user.id, payload.keyword.strip(), payload.count
        )
    except Exception as e:
        return fail(f"岗位采集失败：{e}", code=500)
    if not result.get("collected_count"):
        return fail("本次采集未成功入库任何岗位，请更换关键词后重试", code=502)
    return ok(result, message=f"采集完成：{result['source_label']}，成功 {result['collected_count']} 条")


@router.post("/knowledge/ai-collect")
async def ai_collect_knowledge(
    payload: AICollectKnowledgeRequest,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """AI 采集知识文档：按主题生成结构化文档并走 RAG 链路入库（管理员专属）。"""
    try:
        result = await knowledge_collector.collect_knowledge(
            db, payload.topic.strip(), payload.doc_count
        )
    except Exception as e:
        return fail(f"知识采集失败：{e}", code=500)
    return ok(result, message=f"已生成 {result['generated_count']} 篇知识文档并入库")
