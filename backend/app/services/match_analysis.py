"""匹配度分析服务

提供简历与岗位匹配度分析功能
"""
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Resume, JobAnalysis
from app.models.match import MatchReport, GapItem, Recommendation
from app.tools.match_calculator import calculate_match
from app.schemas.job import JDParsedResult
from app.schemas.match import MatchOut


async def calculate_match_report(
    resume: Resume,
    job: JobAnalysis,
    db: AsyncSession
) -> MatchReport:
    """计算匹配度报告

    Args:
        resume: 简历数据
        job: 岗位数据
        db: 数据库会话

    Returns:
        匹配报告
    """
    # 从工具计算匹配度
    from app.tools.match_calculator import calculate_match
    match_result = calculate_match(resume, job)

    # 创建匹配报告实例
    match_report = MatchReport(
        id=f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{resume.user_id}",
        user_id=resume.user_id,
        job_id=job.id,
        position_title=match_result.position_title,
        skill_match=match_result.skill_match,
        experience_match=match_result.experience_match,
        education_match=match_result.education_match,
        overall_score=match_result.overall_score,
        gaps_json=[gap.model_dump() for gap in match_result.gaps],
        recommendations_json=[rec.model_dump() for rec in match_result.recommendations],
        created_at=datetime.now(),
        analyzed_at=datetime.now()
    )

    return match_report


async def get_match_analysis_history(
    user_id: int,
    db: AsyncSession
) -> List[MatchReport]:
    """获取用户的匹配分析历史"""
    from sqlalchemy import select

    result = await db.execute(
        select(MatchReport)
        .where(MatchReport.user_id == user_id)
        .order_by(MatchReport.analyzed_at.desc())
        .limit(10)
    )
    return result.scalars().all()


async def get_match_detail(
    match_id: str,
    user_id: int,
    db: AsyncSession
) -> MatchReport:
    """获取匹配详情"""
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
    """计算综合匹配分数

    Args:
        match_report: 匹配报告

    Returns:
        综合匹配分数 (0-100)
    """
    # 技能权重50%，经验权重30%，教育权重20%
    overall_score = (
        match_report.skill_match * 0.5 +
        match_report.experience_match * 0.3 +
        match_report.education_match * 0.2
    )
    return overall_score


def get_match_feedback(match_report: MatchReport) -> str:
    """生成匹配反馈

    Args:
        match_report: 匹配报告

    Returns:
        匹配反馈
    """
    feedback_parts = []

    # 技能匹配反馈
    if match_report.skill_match >= 90:
        feedback_parts.append("技能匹配度优秀")
    elif match_report.skill_match >= 70:
        feedback_parts.append("技能匹配度良好")
    elif match_report.skill_match >= 50:
        feedback_parts.append("技能匹配度一般")
    else:
        feedback_parts.append("技能匹配度较低，建议加强技能学习")

    # 经验匹配反馈
    if match_report.experience_match >= 90:
        feedback_parts.append("工作经验丰富")
    elif match_report.experience_match >= 70:
        feedback_parts.append("工作经验匹配较好")
    elif match_report.experience_match >= 50:
        feedback_parts.append("工作经验基本匹配")
    else:
        feedback_parts.append("工作经验不足，建议积累相关经验")

    # 教育匹配反馈
    if match_report.education_match >= 90:
        feedback_parts.append("教育背景符合要求")
    elif match_report.education_match >= 70:
        feedback_parts.append("教育背景基本匹配")
    else:
        feedback_parts.append("教育背景稍显不足")

    # 综合评分
    overall_score = calculate_match_score(match_report)
    if overall_score >= 90:
        feedback_parts.append("整体匹配度优秀，建议投递")
    elif overall_score >= 70:
        feedback_parts.append("整体匹配度良好，可以投递")
    elif overall_score >= 50:
        feedback_parts.append("整体匹配度一般，建议优化后再投递")
    else:
        feedback_parts.append("整体匹配度较低，建议大幅优化后再投递")

    return "，".join(feedback_parts) + "。"


def generate_learning_plan(match_report: MatchReport) -> List[dict]:
    """生成学习计划

    Args:
        match_report: 匹配报告

    Returns:
        学习计划列表
    """
    learning_plan = []

    # 按优先级排序建议
    recommendations = sorted(
        match_report.recommendations,
        key=lambda x: x.priority.value,
        reverse=True
    )

    for i, rec in enumerate(recommendations[:5]):  # 只取前5个建议
        learning_plan.append({
            "id": f"task_{i + 1}",
            "title": rec.description,
            "type": rec.type,
            "priority": rec.priority.value,
            "estimated_time": rec.estimated_time,
            "completed": False
        })

    return learning_plan