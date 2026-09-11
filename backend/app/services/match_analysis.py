"""匹配度分析服务

复用 skill_matcher 规则计算（阶段2 实现），结果映射到 MatchReport ORM：
- 分数：overall_score / skill_match / experience_match / education_match
- 差距：gaps_json + GapItem 关系（type/severity/description）
- 建议：recommendations_json + Recommendation 关系
"""
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Resume, JobAnalysis
from app.models.match import GapItem, MatchReport, Recommendation
from app.tools.job_analyzer import analyze_job_impl
from app.tools.resume_reader import read_resume_impl
from app.tools.skill_matcher import match_skills_impl


async def calculate_match_report(
    resume: Resume,
    job: JobAnalysis,
    db: AsyncSession,
) -> MatchReport:
    """计算匹配度报告：读取用户简历与岗位要求 → 规则计算 → 构造 ORM。"""
    resume_data = await read_resume_impl(db, resume.user_id)
    job_data = await analyze_job_impl(db, job.id)
    result = match_skills_impl(resume_data, job_data)

    if not result.get("matched"):
        raise ValueError(result.get("message", "匹配计算失败：简历或岗位数据缺失"))

    gaps = result.get("gaps", [])

    report = MatchReport(
        id=f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{resume.user_id}",
        user_id=resume.user_id,
        job_id=job.id,
        position_title=job_data.get("position_title") or "未命名岗位",
        skill_match=float(result.get("skill_match", 0)),
        experience_match=float(result.get("experience_match", 0)),
        education_match=float(result.get("education_match", 0)),
        overall_score=float(result.get("overall_score", 0)),
        gaps_json=gaps,
        recommendations_json=[
            {
                "type": g.get("gap_type", "skill"),
                "description": g.get("suggested_action", ""),
                "priority": g.get("priority", "medium"),
            }
            for g in gaps
        ],
        summary=result.get("summary"),
    )

    for g in gaps:
        action = g.get("suggested_action") or f"补齐差距：{g.get('skill_name') or '综合能力'}"
        report.gaps.append(
            GapItem(
                report_id=report.id,
                type=g.get("gap_type", "skill"),
                skill_name=(g.get("skill_name") or None),
                severity=g.get("priority", "medium"),
                description=action,
                current_level=g.get("current_level"),
                target_level=g.get("target_level"),
            )
        )
        report.recommendations.append(
            Recommendation(
                report_id=report.id,
                type=g.get("gap_type", "skill"),
                description=action,
                priority=g.get("priority", "medium"),
            )
        )

    return report


async def get_match_analysis_history(
    user_id: int,
    db: AsyncSession,
) -> List[MatchReport]:
    """获取用户的匹配分析历史。"""
    from sqlalchemy import select

    result = await db.execute(
        select(MatchReport)
        .where(MatchReport.user_id == user_id)
        .order_by(MatchReport.analyzed_at.desc())
        .limit(10)
    )
    return list(result.scalars().all())


async def get_match_detail(
    match_id: str,
    user_id: int,
    db: AsyncSession,
) -> MatchReport:
    """获取匹配详情。"""
    from sqlalchemy import select

    result = await db.scalar(
        select(MatchReport)
        .where(MatchReport.id == match_id)
        .where(MatchReport.user_id == user_id)
    )
    if not result:
        raise Exception("匹配报告不存在")
    return result


def calculate_match_score(match_report: MatchReport) -> float:
    """计算综合匹配分数（0-100）。"""
    return (
        (match_report.skill_match or 0) * 0.5
        + (match_report.experience_match or 0) * 0.3
        + (match_report.education_match or 0) * 0.2
    )


def get_match_feedback(match_report: MatchReport) -> str:
    """生成匹配反馈。"""
    feedback_parts = []

    skill = match_report.skill_match or 0
    exp = match_report.experience_match or 0
    edu = match_report.education_match or 0

    if skill >= 90:
        feedback_parts.append("技能匹配度优秀")
    elif skill >= 70:
        feedback_parts.append("技能匹配度良好")
    elif skill >= 50:
        feedback_parts.append("技能匹配度一般")
    else:
        feedback_parts.append("技能匹配度较低，建议加强技能学习")

    if exp >= 90:
        feedback_parts.append("工作经验丰富")
    elif exp >= 70:
        feedback_parts.append("工作经验匹配较好")
    elif exp >= 50:
        feedback_parts.append("工作经验基本匹配")
    else:
        feedback_parts.append("工作经验不足，建议积累相关经验")

    if edu >= 90:
        feedback_parts.append("教育背景符合要求")
    elif edu >= 70:
        feedback_parts.append("教育背景基本匹配")
    else:
        feedback_parts.append("教育背景稍显不足")

    overall = calculate_match_score(match_report)
    if overall >= 90:
        feedback_parts.append("整体匹配度优秀，建议投递")
    elif overall >= 70:
        feedback_parts.append("整体匹配度良好，可以投递")
    elif overall >= 50:
        feedback_parts.append("整体匹配度一般，建议优化后再投递")
    else:
        feedback_parts.append("整体匹配度较低，建议大幅优化后再投递")

    return "，".join(feedback_parts) + "。"


def generate_learning_plan(match_report: MatchReport) -> List[dict]:
    """根据报告建议生成学习计划列表。"""
    priority_order = {"high": 3, "medium": 2, "low": 1}

    recommendations = sorted(
        match_report.recommendations,
        key=lambda x: priority_order.get(x.priority or "medium", 2),
        reverse=True,
    )

    plan = []
    for i, rec in enumerate(recommendations[:5]):
        plan.append(
            {
                "id": f"task_{i + 1}",
                "title": rec.description,
                "type": rec.type,
                "priority": rec.priority or "medium",
                "estimated_time": rec.estimated_time,
                "completed": False,
            }
        )

    return plan
