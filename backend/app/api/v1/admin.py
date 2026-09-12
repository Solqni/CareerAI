from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.core.response import fail, ok
from app.models import JobAnalysis, KnowledgeDocument, MatchReport, User
from app.schemas.admin import AdminRoleUpdate
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """用户列表（管理员专属）。"""
    users = await db.scalars(select(User).order_by(User.id))
    return ok([UserOut.model_validate(u).model_dump() for u in users])


@router.patch("/users/{user_id}")
async def update_user_role(
    user_id: int,
    payload: AdminRoleUpdate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """修改用户角色（管理员专属）。"""
    target = await db.get(User, user_id)
    if not target:
        return fail("用户不存在", code=404)
    target.role = payload.role
    await db.commit()
    await db.refresh(target)
    return ok(UserOut.model_validate(target).model_dump(), message="角色已更新")


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
