"""能力匹配与学习规划服务（M3，需求 3.3）。

- 匹配度计算与差距识别：复用 match_analysis.calculate_match_report
  （内部走 skill_matcher 规则引擎，输出技能/经验/学历分维度得分与差距明细）
- 学习计划生成（UC-011）：对差距项调用 LLM 生成针对性学习计划与可执行子任务
- 持久化：写入 learning_plan / learning_task 表（含建议资源、预估时长、优先级）
- 任务管理（UC-012）：学习任务状态更新（待开始/进行中/已完成）
"""

import json
import re
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.client import get_chat_llm
from app.models import LearningPlan, LearningTask, MatchReport

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

_PLAN_SYSTEM_PROMPT = (
    "你是学习规划师。根据差距分析为用户生成学习计划，必须输出 JSON，"
    '格式：{"tasks": [{"task_name": "...", "description": "...", '
    '"resource_url": "" 或 null, "priority": "high|medium|low", '
    '"estimated_days": 3}]}，tasks 数量 3-6 个，按优先级排序，'
    "优先补齐 high 优先级差距。仅输出 JSON，不要多余文字。"
)


def _extract_json(text: str) -> dict:
    """从 LLM 输出中容错提取 JSON 对象（与 agents/nodes.py 同策略）。"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {"tasks": []}
    except json.JSONDecodeError:
        return {"tasks": []}


def _normalize_tasks(raw: dict) -> list[dict]:
    """校验并规整 LLM 返回的任务列表。"""
    tasks = raw.get("tasks") if isinstance(raw, dict) else None
    if not isinstance(tasks, list):
        return []
    result = []
    for t in tasks:
        if not isinstance(t, dict) or not t.get("task_name"):
            continue
        priority = t.get("priority")
        result.append(
            {
                "task_name": str(t["task_name"])[:255],
                "description": str(t.get("description") or "") or None,
                "resource_url": (str(t.get("resource_url")) if t.get("resource_url") else None),
                "priority": priority if priority in PRIORITY_ORDER else "medium",
                "estimated_days": int(t["estimated_days"]) if t.get("estimated_days") else None,
            }
        )
    return result[:6]


def _rule_based_tasks(report: MatchReport) -> list[dict]:
    """LLM 失败时的降级方案：按报告建议生成任务（保证功能可用）。"""
    recommendations = sorted(
        (report.recommendations or []),
        key=lambda r: PRIORITY_ORDER.get(r.priority or "medium", 1),
    )
    return [
        {
            "task_name": (r.description or "补齐能力差距")[:255],
            "description": r.description,
            "resource_url": None,
            "priority": r.priority if r.priority in PRIORITY_ORDER else "medium",
            "estimated_days": None,
        }
        for r in recommendations[:5]
    ]


async def _llm_plan_tasks(gaps: list[dict], position_title: str) -> list[dict]:
    """调用 LLM 针对差距清单生成学习任务（UC-011）。"""
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_chat_llm()
    resp = await llm.ainvoke(
        [
            SystemMessage(_PLAN_SYSTEM_PROMPT),
            HumanMessage(
                f"目标岗位：{position_title or '未命名岗位'}\n"
                f"差距分析：\n{json.dumps(gaps, ensure_ascii=False)}"
            ),
        ]
    )
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    return _normalize_tasks(_extract_json(content))


async def llm_match_analysis(report: MatchReport) -> str | None:
    """LLM 基于规则引擎的匹配数据生成综合文字分析（需求 3.3.2）。

    评分保持规则计算（可解释、确定性强），LLM 只负责综合研判：
    整体判断 → 核心优势 → 最需补齐短板 → 投递建议。
    失败返回 None，由调用方降级为规则 summary。
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    data = {
        "position_title": report.position_title,
        "overall_score": report.overall_score,
        "skill_match": report.skill_match,
        "experience_match": report.experience_match,
        "education_match": report.education_match,
        "gaps": report.gaps_json or [],
    }
    llm = get_chat_llm()
    resp = await llm.ainvoke(
        [
            SystemMessage(
                "你是资深职业规划顾问。基于给定的人岗匹配数据（分维度得分与差距明细），"
                "输出 3-5 句简明的综合分析（中文）：先给整体匹配判断，"
                "再指出核心优势与最需补齐的短板，最后给出是否建议投递及理由。"
                "直接输出文字，不要 JSON、不要标题符号。"
            ),
            HumanMessage(json.dumps(data, ensure_ascii=False)),
        ]
    )
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    content = content.strip()
    return content or None


async def generate_and_persist_plan(
    report: MatchReport, db: AsyncSession
) -> LearningPlan | None:
    """对匹配报告生成学习计划并写入 learning_plan + learning_task。

    LLM 失败时降级为规则生成（基于报告建议），保证 UC-011 可用。
    仅 flush 不 commit（与匹配报告同一事务，由调用方统一提交）。
    """
    gaps = report.gaps_json or []

    tasks: list[dict] = []
    source = "llm"
    try:
        tasks = await _llm_plan_tasks(gaps, report.position_title)
    except Exception:
        tasks = []
    if not tasks:
        tasks = _rule_based_tasks(report)
        source = "fallback"
    if not tasks:
        return None

    plan = LearningPlan(
        user_id=report.user_id,
        report_id=report.id,
        content_json={"tasks": tasks, "source": source},
        status="active",
    )
    db.add(plan)
    await db.flush()

    for t in sorted(tasks, key=lambda x: PRIORITY_ORDER.get(x.get("priority", "medium"), 1)):
        days = t.get("estimated_days")
        due = (
            (date.today() + timedelta(days=int(days))).isoformat() if days else None
        )
        db.add(
            LearningTask(
                plan_id=plan.id,
                task_name=t["task_name"],
                description=t.get("description"),
                resource_url=t.get("resource_url"),
                priority=t.get("priority", "medium"),
                estimated_days=days,
                status="todo",
                due_date=due,
            )
        )
    await db.flush()
    return plan


async def get_plan_by_report(
    match_id: str, user_id: int, db: AsyncSession
) -> LearningPlan | None:
    """按匹配报告查询学习计划（含任务列表）。"""
    return await db.scalar(
        select(LearningPlan)
        .where(LearningPlan.report_id == match_id)
        .where(LearningPlan.user_id == user_id)
        .options(selectinload(LearningPlan.tasks))
        .order_by(LearningPlan.id.desc())
    )


async def update_task_status(
    task_id: int, user_id: int, new_status: str, db: AsyncSession
) -> LearningTask | None:
    """更新学习任务状态（UC-012），校验任务归属当前用户。"""
    task = await db.scalar(
        select(LearningTask)
        .join(LearningPlan, LearningTask.plan_id == LearningPlan.id)
        .where(LearningTask.id == task_id)
        .where(LearningPlan.user_id == user_id)
    )
    if not task:
        return None
    task.status = new_status
    await db.commit()
    await db.refresh(task)
    return task
