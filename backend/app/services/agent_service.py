"""Agent 业务编排层：运行工作流 → 结果持久化 → 会话记忆。

- 运行 LangGraph 工作流（analyze → match → plan → output）
- 将匹配报告 / 差距项 / 学习计划 / 学习任务写入对应数据表
- 通过 conversation + message 表持久化 Agent 会话（需求 7.1 短期记忆）
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import career_graph
from app.models import (
    Conversation,
    GapItem,
    LearningPlan,
    LearningTask,
    MatchReport,
    Message,
)
from app.tools.job_analyzer import analyze_job_impl
from app.tools.resume_reader import read_resume_impl

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


async def run_career_agent(db: AsyncSession, user_id: int, job_id: int) -> dict:
    """执行完整 Agent 工作流并持久化结果。"""
    # 1. 运行 LangGraph 工作流
    state = await career_graph.ainvoke({"user_id": user_id, "job_id": job_id})
    report = state.get("report", {})

    # 2. 前置数据校验失败 → 不入库，直接返回失败报告
    if not report.get("success"):
        return {"report": report, "report_id": None, "plan_id": None}

    # 3. 持久化匹配报告
    match_report = MatchReport(
        user_id=user_id,
        job_id=job_id,
        total_score=report.get("overall_score", 0),
        summary=report.get("analysis"),
        detail_json={
            "skill_match": report.get("skill_match"),
            "experience_match": report.get("experience_match"),
            "education_match": report.get("education_match"),
            "gaps": report.get("gaps", []),
            "knowledge_sources": report.get("knowledge_sources", []),
            "agent_errors": report.get("errors", []),
        },
    )
    db.add(match_report)
    await db.flush()

    # 4. 持久化差距项
    for gap in report.get("gaps", []):
        db.add(
            GapItem(
                report_id=match_report.id,
                gap_type=gap.get("gap_type", "skill"),
                skill_name=(gap.get("skill_name") or "综合能力")[:128],
                priority=gap.get("priority", "medium"),
                suggested_action=gap.get("suggested_action"),
            )
        )

    # 5. 持久化学习计划与任务
    plan_id: int | None = None
    tasks = report.get("plan", [])
    if tasks:
        plan = LearningPlan(
            user_id=user_id,
            report_id=match_report.id,
            content_json={"tasks": tasks},
            status="active",
        )
        db.add(plan)
        await db.flush()
        plan_id = plan.id

        for task in sorted(
            tasks, key=lambda t: PRIORITY_ORDER.get(t.get("priority", "medium"), 1)
        ):
            db.add(
                LearningTask(
                    plan_id=plan.id,
                    task_name=(task.get("task_name") or "未命名任务")[:255],
                    description=task.get("description"),
                    resource_url=task.get("resource_url"),
                    status="todo",
                    due_date=None,
                )
            )

    await db.commit()
    return {"report": report, "report_id": match_report.id, "plan_id": plan_id}


async def ensure_conversation(
    db: AsyncSession, user_id: int, conversation_id: int | None
) -> Conversation:
    """获取或创建 Agent 会话（多轮对话记忆载体）。"""
    if conversation_id:
        conv = await db.scalar(select(Conversation).where(Conversation.id == conversation_id))
        if conv and conv.user_id == user_id:
            return conv
    conv = Conversation(user_id=user_id, title="职业助手对话", agent_type="career")
    db.add(conv)
    await db.flush()
    return conv


async def load_history(db: AsyncSession, conversation_id: int, limit: int = 10) -> list[Message]:
    """加载会话历史消息（短期记忆来源）。"""
    rows = await db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    return list(reversed(list(rows)))


async def build_context_with_tools(
    db: AsyncSession, user_id: int, conversation_id: int, question: str
) -> dict:
    """对话式交互：加载记忆 → 按需调用工具 → LLM 生成回答（简化 ReAct 模式）。"""
    conv = await ensure_conversation(db, user_id, conversation_id)
    history = await load_history(db, conv.id)

    # 关键词触发工具调用（轻量意图路由）
    tool_observations: list[str] = []
    try:
        lowered = question.lower()
        if any(k in lowered for k in ("简历", "技能", "经历", "我的")):
            resume = await read_resume_impl(db, user_id)
            tool_observations.append(f"[resume_reader] {resume}")
        if any(k in lowered for k in ("岗位", "jd", "要求", "招聘")):
            # 取用户最近一个岗位
            from app.models import JobAnalysis

            job = await db.scalar(
                select(JobAnalysis)
                .where(JobAnalysis.user_id == user_id)
                .order_by(JobAnalysis.id.desc())
                .limit(1)
            )
            if job:
                job_info = await analyze_job_impl(db, job.id)
                tool_observations.append(f"[job_analyzer] {job_info}")
        if any(k in lowered for k in ("怎么学", "资料", "学习", "资源", "怎么准备")):
            from app.tools.knowledge_searcher import search_knowledge_impl

            hits = await search_knowledge_impl(db, question, top_k=3)
            tool_observations.append(
                f"[knowledge_searcher] {[{k: h[k] for k in ('doc_title', 'content')} for h in hits]}"
            )
    except Exception as e:  # Tool 失败不影响对话
        tool_observations.append(f"[tool_error] {e}")

    # 组装上下文：记忆 + 工具观察
    history_text = "\n".join(f"{m.role}: {m.content}" for m in history if m.content)
    observation_text = "\n".join(tool_observations) if tool_observations else "（无）"

    from app.llm.client import get_chat_llm

    llm = get_chat_llm()
    resp = await llm.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "你是 CareerAI 职业成长助手，能引用之前对话上下文与工具查询结果回答问题。"
                    "回答用中文，简洁专业。\n\n"
                    f"【对话历史（短期记忆）】\n{history_text or '（新会话）'}\n\n"
                    f"【工具查询结果】\n{observation_text}"
                ),
            },
            {"role": "user", "content": question},
        ]
    )
    answer = resp.content if isinstance(resp.content, str) else str(resp.content)

    # 持久化本轮消息
    db.add(Message(conversation_id=conv.id, role="user", content=question))
    db.add(
        Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            tool_calls={"tools": tool_observations} if tool_observations else None,
        )
    )
    await db.commit()

    return {"conversation_id": conv.id, "answer": answer, "tools_used": len(tool_observations)}
