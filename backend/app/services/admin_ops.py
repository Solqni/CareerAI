"""管理员运维服务：用户删除（级联清理全部业务数据）、岗位级联删除。

级联依赖链（FK 均无数据库级 ondelete，需按序手动删除）：
user ← user_skill / user_experience / resume / job_analysis ← job_requirement
job_analysis ← match_report ← gap_item / recommendation / learning_plan ← learning_task
user ← conversation ← message；user ← interview_session ← interview_qa
"""

import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Conversation,
    GapItem,
    InterviewQA,
    InterviewSession,
    JobAnalysis,
    JobRequirement,
    LearningPlan,
    LearningTask,
    MatchReport,
    Message,
    Recommendation,
    Resume,
    User,
    UserExperience,
    UserSkill,
)

logger = logging.getLogger(__name__)


async def count_admins(db: AsyncSession) -> int:
    return await db.scalar(
        select(func.count(User.id)).where(User.role == "admin")
    ) or 0


async def delete_job_cascade(db: AsyncSession, job_ids: list[int]) -> None:
    """删除岗位及其全部关联数据（要求/匹配报告链）。"""
    if not job_ids:
        return
    report_ids = [
        rid for (rid,) in await db.execute(
            select(MatchReport.id).where(MatchReport.job_id.in_(job_ids))
        )
    ]
    if report_ids:
        plan_ids = [
            pid for (pid,) in await db.execute(
                select(LearningPlan.id).where(LearningPlan.report_id.in_(report_ids))
            )
        ]
        if plan_ids:
            await db.execute(delete(LearningTask).where(LearningTask.plan_id.in_(plan_ids)))
        await db.execute(delete(LearningPlan).where(LearningPlan.report_id.in_(report_ids)))
        await db.execute(delete(GapItem).where(GapItem.report_id.in_(report_ids)))
        await db.execute(delete(Recommendation).where(Recommendation.report_id.in_(report_ids)))
        await db.execute(delete(MatchReport).where(MatchReport.id.in_(report_ids)))
    await db.execute(delete(JobRequirement).where(JobRequirement.job_id.in_(job_ids)))
    # 岗位可能被面试会话引用（如共享岗位）：解除关联，保留用户面试记录
    await db.execute(
        update(InterviewSession)
        .where(InterviewSession.job_id.in_(job_ids))
        .values(job_id=None)
    )
    await db.execute(delete(JobAnalysis).where(JobAnalysis.id.in_(job_ids)))


async def delete_user_cascade(db: AsyncSession, user_id: int) -> None:
    """删除用户及其全部业务数据（含其岗位的报告链、面试会话、对话记忆）。"""
    job_ids = [
        jid for (jid,) in await db.execute(
            select(JobAnalysis.id).where(JobAnalysis.user_id == user_id)
        )
    ]
    # 该用户名下报告（不论挂在谁的岗位下）+ 其岗位关联的报告
    report_id_rows = await db.execute(
        select(MatchReport.id).where(
            (MatchReport.user_id == user_id) | (MatchReport.job_id.in_(job_ids or [0]))
        )
    )
    report_ids = [rid for (rid,) in report_id_rows]

    plan_ids = [
        pid for (pid,) in await db.execute(
            select(LearningPlan.id).where(
                (LearningPlan.user_id == user_id) | (LearningPlan.report_id.in_(report_ids or [""]))
            )
        )
    ]
    if plan_ids:
        await db.execute(delete(LearningTask).where(LearningTask.plan_id.in_(plan_ids)))
    await db.execute(
        delete(LearningPlan).where(
            (LearningPlan.user_id == user_id) | (LearningPlan.report_id.in_(report_ids or [""]))
        )
    )
    if report_ids:
        await db.execute(delete(GapItem).where(GapItem.report_id.in_(report_ids)))
        await db.execute(delete(Recommendation).where(Recommendation.report_id.in_(report_ids)))
    await db.execute(
        delete(MatchReport).where(
            (MatchReport.user_id == user_id) | (MatchReport.job_id.in_(job_ids or [0]))
        )
    )

    session_ids = [
        sid for (sid,) in await db.execute(
            select(InterviewSession.id).where(InterviewSession.user_id == user_id)
        )
    ]
    if session_ids:
        await db.execute(delete(InterviewQA).where(InterviewQA.session_id.in_(session_ids)))
    await db.execute(delete(InterviewSession).where(InterviewSession.user_id == user_id))

    conversation_ids = [
        cid for (cid,) in await db.execute(
            select(Conversation.id).where(Conversation.user_id == user_id)
        )
    ]
    if conversation_ids:
        await db.execute(delete(Message).where(Message.conversation_id.in_(conversation_ids)))
    await db.execute(delete(Conversation).where(Conversation.user_id == user_id))

    await delete_job_cascade(db, job_ids)
    await db.execute(delete(Resume).where(Resume.user_id == user_id))
    await db.execute(delete(UserSkill).where(UserSkill.user_id == user_id))
    await db.execute(delete(UserExperience).where(UserExperience.user_id == user_id))
    await db.execute(delete(User).where(User.id == user_id))
