"""能力匹配与学习规划服务（M3，需求 3.3）。

- 匹配度计算与差距识别：复用 match_analysis.calculate_match_report
  （内部走 skill_matcher 规则引擎，输出技能/经验/学历分维度得分与差距明细）
- 学习计划生成（UC-011）：对差距项调用 LLM 生成针对性学习计划与可执行子任务
- 持久化：写入 learning_plan / learning_task 表（含建议资源、预估时长、优先级）
- 任务管理（UC-012）：学习任务状态更新（待开始/进行中/已完成）
"""

import json
import logging
import re
from datetime import date, timedelta

from langchain_core.messages import HumanMessage, SystemMessage
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


_STUDY_SYSTEM_PROMPT = (
    "你是学习教练。根据学习任务与知识库片段为用户生成练习题，必须输出 JSON，"
    '格式：{"questions": [{"question": "...", "reference_answer": "..."}]}。要求：\n'
    "1. 题目 3-5 道，紧扣任务涉及的知识点（优先结合知识库片段内容）；\n"
    "2. 题型为简答/场景分析，能检验掌握程度，不要选择题；\n"
    "3. reference_answer 简明准确，每题 2-4 句；\n"
    "4. 仅输出 JSON，不要多余文字。"
)

_ANSWER_SYSTEM_PROMPT = (
    "你是练习题批改教练。根据题目、参考答案与用户作答给出点评，必须输出 JSON，"
    '格式：{"score": 0到100的整数, "feedback": "点评文字"}。要求：\n'
    "1. 先肯定答对的部分，再指出遗漏或错误，最后给一句改进建议；\n"
    "2. feedback 简明 2-4 句，语气温和鼓励；\n"
    "3. 仅输出 JSON，不要多余文字。"
)


def _normalize_questions(raw: dict) -> list[dict]:
    """校验并规整 LLM 返回的练习题列表。"""
    questions = raw.get("questions") if isinstance(raw, dict) else None
    if not isinstance(questions, list):
        return []
    result = []
    for q in questions:
        if not isinstance(q, dict) or not q.get("question"):
            continue
        result.append(
            {
                "question": str(q["question"]),
                "reference_answer": str(q.get("reference_answer") or ""),
            }
        )
    return result[:5]


def _study_cache(task: LearningTask) -> dict:
    """读取 study_json 缓存并补齐默认结构（兼容旧数据）。"""
    cache = task.study_json if isinstance(task.study_json, dict) else {}
    cache.setdefault("questions", [])
    cache.setdefault("asked", [])
    cache.setdefault("answers", {})
    cache.setdefault("batch", 1)
    cache.setdefault("total_generated", 0)
    # 旧格式缓存没有累计字段，用当前批题数兜底
    if cache["total_generated"] < len(cache["questions"]):
        cache["total_generated"] = len(cache["questions"])
    return cache


async def _generate_questions(
    task: LearningTask, knowledge: list[dict], avoid: list[str]
) -> list[dict]:
    """调用 LLM 生成一批练习题，avoid 中的题目不再重复出现。"""
    context = "\n\n".join(
        f"[片段{i + 1}]（来源：{k['doc_title']}）\n{k['content']}"
        for i, k in enumerate(knowledge)
    ) or "（无知识库片段，请基于通用知识出题）"
    avoid_text = (
        "\n\n出题时必须避开以下已出过的题目（考察角度也不要重复）：\n"
        + "\n".join(f"- {q}" for q in avoid[-30:])
        if avoid
        else ""
    )
    llm = get_chat_llm()
    resp = await llm.ainvoke(
        [
            SystemMessage(_STUDY_SYSTEM_PROMPT),
            HumanMessage(
                f"学习任务：{task.task_name}\n"
                f"任务描述：{task.description or '（无）'}\n\n"
                f"知识库片段：\n{context}{avoid_text}"
            ),
        ]
    )
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    return _normalize_questions(_extract_json(content))


def _study_result(task: LearningTask, knowledge: list[dict], cache: dict, source: str) -> dict:
    """组装学习内容返回值（统一结构，供查询/换新题/答题后复用）。"""
    return {
        "task_id": task.id,
        "task_name": task.task_name,
        "knowledge": knowledge,
        "questions": cache.get("questions", []),
        "answers": cache.get("answers", {}),
        "batch": cache.get("batch", 1),
        "total_generated": cache.get("total_generated", 0),
        "source": source,
    }


async def _load_task(task_id: int, user_id: int, db: AsyncSession) -> LearningTask | None:
    return await db.scalar(
        select(LearningTask)
        .join(LearningPlan, LearningTask.plan_id == LearningPlan.id)
        .where(LearningTask.id == task_id)
        .where(LearningPlan.user_id == user_id)
    )


async def _retrieve_knowledge(task: LearningTask, db: AsyncSession) -> list[dict]:
    """RAG 实时检索关联知识点（失败降级为空列表，不阻断）。"""
    from app.services.rag import search_knowledge

    try:
        query = " ".join([task.task_name, task.description or ""]).strip()
        if not query:
            return []
        hits = await search_knowledge(db, query, top_k=4)
        return [
            {
                "doc_title": h["doc_title"],
                "content": h["content"],
                "similarity": h["similarity"],
            }
            for h in hits
        ]
    except Exception:
        logging.getLogger(__name__).exception("学习内容知识库检索失败，返回空知识点")
        return []


async def get_task_study(task_id: int, user_id: int, db: AsyncSession) -> dict | None:
    """学习任务的学习内容：RAG 实时检索关联知识点（管理员知识库）+ 当前一批练习题。

    练习题由 LLM 生成并缓存到 task.study_json（questions 为当前批，asked 为历史全部，
    answers 为作答记录）。再次查看直接复用缓存（source=cache）。
    任务不存在或不属于该用户返回 None。
    """
    task = await _load_task(task_id, user_id, db)
    if not task:
        return None

    knowledge = await _retrieve_knowledge(task, db)
    cache = _study_cache(task)

    # 首次查看且无缓存题目：生成第一批（写缓存统一由生成成功路径处理）
    if not cache["questions"]:
        try:
            questions = await _generate_questions(task, knowledge, cache["asked"])
            if questions:
                cache["questions"] = questions
                cache["source"] = "llm"
                cache["total_generated"] = int(cache["total_generated"]) + len(questions)
                task.study_json = cache
                await db.commit()
        except Exception:
            logging.getLogger(__name__).exception(
                "学习任务 %s 练习题生成失败，本次降级仅返回知识点", task_id
            )  # 生成失败降级为仅知识点，下次查看或重试出题再试

    return _study_result(task, knowledge, cache, cache.get("source", "rag_only"))


async def refresh_task_study(task_id: int, user_id: int, db: AsyncSession) -> dict | None:
    """换一批新题：当前批题目并入历史，LLM 生成一批不与历史重复的新题并清空作答记录。

    LLM 失败抛 ValueError（旧缓存保留，不影响再次查看）。
    """
    task = await _load_task(task_id, user_id, db)
    if not task:
        return None

    knowledge = await _retrieve_knowledge(task, db)
    cache = _study_cache(task)

    asked: list[str] = list(cache["asked"])
    asked += [q["question"] for q in cache["questions"] if q.get("question")]

    questions = await _generate_questions(task, knowledge, asked)
    if not questions:
        raise ValueError("新题目生成失败，请稍后重试")

    cache["questions"] = questions
    cache["asked"] = asked
    cache["answers"] = {}
    cache["source"] = "llm"
    cache["batch"] = int(cache["batch"]) + 1
    cache["total_generated"] = int(cache["total_generated"]) + len(questions)
    task.study_json = cache
    await db.commit()
    return _study_result(task, knowledge, cache, "llm")


async def answer_task_question(
    task_id: int, user_id: int, db: AsyncSession, question: str, answer: str
) -> dict | None:
    """提交练习题作答：LLM 对比参考答案给出得分与点评，持久化到 study_json.answers。

    任务不存在 / 题目不在当前批 / 作答为空返回 None；LLM 失败抛 ValueError。
    """
    task = await _load_task(task_id, user_id, db)
    if not task:
        return None
    question = (question or "").strip()
    answer = (answer or "").strip()
    if not question or not answer:
        return None

    cache = _study_cache(task)
    target = next(
        (q for q in cache["questions"] if q.get("question") == question), None
    )
    if not target:
        return None

    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_chat_llm()
    resp = await llm.ainvoke(
        [
            SystemMessage(_ANSWER_SYSTEM_PROMPT),
            HumanMessage(
                f"题目：{question}\n\n"
                f"参考答案：{target.get('reference_answer') or '（无）'}\n\n"
                f"用户作答：{answer}"
            ),
        ]
    )
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    raw = _extract_json(content)
    try:
        score = max(0, min(100, int(raw.get("score"))))
    except (TypeError, ValueError):
        score = None
    feedback = str(raw.get("feedback") or "").strip()
    if not feedback:
        raise ValueError("点评生成失败，请稍后重试")

    cache.setdefault("answers", {})[question] = {
        "answer": answer,
        "feedback": feedback,
        "score": score,
    }
    task.study_json = cache
    await db.commit()
    return {
        "question": question,
        "answer": answer,
        "feedback": feedback,
        "score": score,
    }
