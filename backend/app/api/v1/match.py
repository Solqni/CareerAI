from fastapi import APIRouter, Depends, HTTPException
import logging

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models import JobAnalysis, LearningPlan, MatchReport, Resume, User
from app.schemas.match import (
    LearningPlanOut,
    LearningTaskOut,
    MatchCreate,
    MatchOut,
    TaskStatusUpdate,
)
from app.services.match_analysis import calculate_match_report
from app.services.matching import (
    generate_and_persist_plan,
    get_plan_by_report,
    llm_match_analysis,
    update_task_status,
)

router = APIRouter(prefix="/match", tags=["match"])
logger = logging.getLogger(__name__)

# 报告完整预加载：差距 + 建议 + 学习计划（含任务），避免 commit 后懒加载 MissingGreenlet
_REPORT_LOAD = (
    selectinload(MatchReport.gaps),
    selectinload(MatchReport.recommendations),
    selectinload(MatchReport.learning_plan).selectinload(LearningPlan.tasks),
)


async def _run_full_match(
    payload: MatchCreate, current_user: User, db: AsyncSession
) -> MatchReport:
    """完整匹配流程（需求 3.3 UC-008~011）：

    1. 校验简历与岗位归属（UC-008 前置）
    2. skill_matcher 规则计算匹配度与差距（UC-008/009，分维度可解释）
    3. 持久化 match_report + gap_item + recommendation
    4. LLM 生成学习计划并持久化 learning_plan + learning_task（UC-011）
    """
    resume = await db.scalar(
        select(Resume)
        .where(Resume.id == payload.resume_id)
        .where(Resume.user_id == current_user.id)
    )
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    job = await db.scalar(
        select(JobAnalysis)
        .where(JobAnalysis.id == payload.job_id)
        .where(
            or_(
                JobAnalysis.user_id == current_user.id,
                JobAnalysis.is_shared.is_(True),
            )
        )
    )
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # commit 后 ORM 关系过期，此处暂存岗位公司/城市，供重查后挂载到报告上
    job_parsed = job.parsed_json or {}

    # 1-3. 匹配计算 + 报告/差距/建议 ORM 构造
    report = await calculate_match_report(resume, job, db)

    # 需求 3.3.2：LLM 基于规则计算结果生成综合文字分析（失败降级保留规则 summary）
    rule_summary = report.summary
    try:
        analysis = await llm_match_analysis(report)
        if analysis:
            report.summary = analysis
            report.detail_json = {"analysis_source": "llm", "rule_summary": rule_summary}
    except Exception:
        logger.exception("LLM 综合分析生成失败，降级为规则 summary")
        report.detail_json = {"analysis_source": "rule"}

    db.add(report)
    await db.flush()  # 先取 report.id，供 learning_plan 关联

    # 4. 学习计划生成（LLM，失败自动降级为规则生成；异常时回滚计划仅保留报告）
    try:
        await generate_and_persist_plan(report, db)
    except Exception:
        await db.rollback()
        db.add(report)

    # 单次事务提交：报告 + 差距 + 建议 + 学习计划
    await db.commit()

    # commit 后关系过期，重查（项目约定）
    result = await db.scalar(
        select(MatchReport).where(MatchReport.id == report.id).options(*_REPORT_LOAD)
    )
    # 挂载岗位公司/城市与分析来源（表无这些列，供 Pydantic from_attributes 读取）
    result.company = job_parsed.get("company")
    result.city = job_parsed.get("city")
    result.analysis_source = (result.detail_json or {}).get("analysis_source")
    return result


@router.post("", response_model=MatchOut)
async def create_match(
    payload: MatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """触发完整匹配流程：匹配度计算 → 差距识别 → 学习计划生成，返回匹配报告。"""
    return await _run_full_match(payload, current_user, db)


@router.post("/analyze", response_model=MatchOut)
async def analyze_match(
    payload: MatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """分析简历与岗位的匹配度（与 POST /match 等价，兼容前端既有调用）。"""
    return await _run_full_match(payload, current_user, db)


@router.get("/")
async def list_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取匹配报告列表"""
    result = await db.execute(
        select(MatchReport)
        .where(MatchReport.user_id == current_user.id)
        .order_by(MatchReport.analyzed_at.desc())
        .limit(10)
    )
    return {"user_id": current_user.id, "reports": result.scalars().all()}


@router.get("/{match_id}", response_model=MatchOut)
async def get_match_detail(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取匹配详情（含差距、建议与学习计划）"""
    result = await db.scalar(
        select(MatchReport)
        .where(MatchReport.id == match_id)
        .where(MatchReport.user_id == current_user.id)
        .options(*_REPORT_LOAD)
    )
    if not result:
        raise HTTPException(status_code=404, detail="匹配报告不存在")

    # 补充岗位公司/城市（岗位可能已删除，判空不挂载）与分析来源
    job = await db.scalar(select(JobAnalysis).where(JobAnalysis.id == result.job_id))
    if job:
        job_parsed = job.parsed_json or {}
        result.company = job_parsed.get("company")
        result.city = job_parsed.get("city")
    result.analysis_source = (result.detail_json or {}).get("analysis_source")
    return result


@router.get("/{match_id}/plan", response_model=LearningPlanOut)
async def get_match_plan(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取匹配报告对应的学习计划与任务列表（UC-011/UC-012）"""
    plan = await get_plan_by_report(match_id, current_user.id, db)
    if not plan:
        raise HTTPException(status_code=404, detail="该报告暂无学习计划")
    return plan


@router.patch("/plan/tasks/{task_id}", response_model=LearningTaskOut)
async def update_learning_task(
    task_id: int,
    payload: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新学习任务状态：todo（待开始）/ in_progress（进行中）/ done（已完成）（UC-012）"""
    task = await update_task_status(task_id, current_user.id, payload.status.value, db)
    if not task:
        raise HTTPException(status_code=404, detail="学习任务不存在")
    return task
