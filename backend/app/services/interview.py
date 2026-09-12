"""面试准备服务（M5，需求 3.5）。

核心流程：
1. 面试题生成：复用 tools.interview_helper.generate_interview_q_impl，
   基于岗位要求 + 用户简历由 LLM 生成技术/项目/行为三类题目，失败有兜底题库；
2. 模拟面试：创建 interview_session，题目落 interview_qa，
   Agent 扮演面试官逐轮提问，用户多轮文本作答；
3. 答案评估：每轮回答由 LLM 从逻辑性、完整性、专业性三维度打分，
   并给出优点、不足、改进建议，写回 interview_qa（score/feedback/feedback_json）；
4. 反馈报告：面试结束后 LLM 汇总所有轮次生成总评，写入 session.summary。

多轮上下文（需求 7.1 Memory）：每轮评估前从 interview_qa 表加载历史问答，
让面试官的评估能引用前面的对话。
"""

import json
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.client import get_chat_llm
from app.models import InterviewQA, InterviewSession, JobAnalysis, Resume
from app.tools.interview_helper import generate_interview_q_impl
from app.tools.job_analyzer import analyze_job_impl

logger = logging.getLogger(__name__)

_MAX_ANSWER_CHARS = 2000
_SESSION_LOAD = selectinload(InterviewSession.qas)

_EVAL_SYSTEM_PROMPT = (
    "你是资深技术面试官，正在对候选人的模拟面试回答做评分。"
    "必须输出 JSON，格式："
    '{"logic": 0-100整数, "completeness": 0-100整数, '
    '"professionalism": 0-100整数, "overall": 0-100整数, '
    '"strengths": "优点（中文，1-2句）", '
    '"weaknesses": "不足（中文，1-2句）", '
    '"suggestions": "改进建议（中文，1-2句）"}。\n'
    "评分维度：logic=逻辑性（结构是否清晰、论证是否自洽），"
    "completeness=完整性（是否切题、要点是否覆盖），"
    "professionalism=专业性（技术深度、术语与实践经验）。"
    "回答过于简短或明显敷衍时给低分。仅输出 JSON，不要多余文字。"
)

_SUMMARY_SYSTEM_PROMPT = (
    "你是资深技术面试官。基于候选人本场模拟面试的全部问答与逐轮评分，"
    "输出 200-400 字的中文总评报告，内容依次包括："
    "整体表现判断、突出优点、主要不足、针对性备考建议（按重要性排序）。"
    "直接输出报告正文，可以分段，不要 JSON、不要客套话。"
)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict:
    """从 LLM 输出中容错提取 JSON 对象（与 services/matching.py 同策略）。"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _clamp_score(value) -> int:
    """把 LLM 返回的分数规整为 0-100 整数。"""
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return 60
    return max(0, min(100, score))


def serialize_qa(qa: InterviewQA) -> dict:
    return {
        "id": qa.id,
        "session_id": qa.session_id,
        "category": qa.category,
        "question": qa.question,
        "answer": qa.answer,
        "score": qa.score,
        "feedback": qa.feedback,
        "feedback_json": qa.feedback_json,
    }


async def _position_title(db: AsyncSession, job_id: int | None) -> str | None:
    if not job_id:
        return None
    job = await db.scalar(select(JobAnalysis).where(JobAnalysis.id == job_id))
    if not job or not job.parsed_json:
        return None
    return job.parsed_json.get("position_title")


async def serialize_session(db: AsyncSession, session: InterviewSession) -> dict:
    return {
        "id": session.id,
        "user_id": session.user_id,
        "job_id": session.job_id,
        "resume_id": session.resume_id,
        "position_title": await _position_title(db, session.job_id),
        "status": session.status,
        "summary": session.summary,
        "created_at": session.created_at,
        "finished_at": session.finished_at,
        "qas": [serialize_qa(qa) for qa in session.qas],
    }


async def _get_owned_session(
    db: AsyncSession, user_id: int, session_id: int
) -> InterviewSession | None:
    """查询会话（含问答），并校验归属。"""
    return await db.scalar(
        select(InterviewSession)
        .where(InterviewSession.id == session_id)
        .where(InterviewSession.user_id == user_id)
        .options(_SESSION_LOAD)
    )


async def _resolve_resume_id(
    db: AsyncSession, user_id: int, resume_id: int | None
) -> int | None:
    """校验指定简历归属；未指定时取用户最新简历。"""
    if resume_id:
        owned = await db.scalar(
            select(Resume.id)
            .where(Resume.id == resume_id)
            .where(Resume.user_id == user_id)
        )
        return owned
    latest = await db.scalar(
        select(Resume.id)
        .where(Resume.user_id == user_id)
        .order_by(Resume.id.desc())
        .limit(1)
    )
    return latest


# ---------------------------------------------------------------------------
# 业务流程
# ---------------------------------------------------------------------------


async def generate_questions(
    db: AsyncSession,
    user_id: int,
    job_id: int,
    resume_id: int | None = None,
    question_count: int = 6,
) -> dict:
    """仅生成面试题（需求 3.5 第 1 项），校验岗位归属。"""
    job = await db.scalar(
        select(JobAnalysis)
        .where(JobAnalysis.id == job_id)
        .where(JobAnalysis.user_id == user_id)
    )
    if not job:
        raise ValueError("岗位不存在或无权访问")

    resolved_resume_id = await _resolve_resume_id(db, user_id, resume_id)
    result = await generate_interview_q_impl(
        db, job_id, resolved_resume_id, question_count
    )
    if not result.get("found"):
        raise ValueError("岗位不存在或无权访问")
    return {
        "job_id": job_id,
        "position_title": result.get("position_title"),
        "questions": result.get("questions", []),
        "source": result.get("source", "llm"),
    }


async def create_session(
    db: AsyncSession,
    user_id: int,
    job_id: int,
    resume_id: int | None = None,
    question_count: int = 6,
) -> dict:
    """创建模拟面试会话：生成题库并落 interview_qa（岗位可访问：自有或平台共享）。"""
    job = await db.scalar(
        select(JobAnalysis)
        .where(JobAnalysis.id == job_id)
        .where(
            or_(
                JobAnalysis.user_id == user_id,
                JobAnalysis.is_shared.is_(True),
            )
        )
    )
    if not job:
        raise ValueError("岗位不存在或无权访问")

    resolved_resume_id = await _resolve_resume_id(db, user_id, resume_id)

    result = await generate_interview_q_impl(
        db, job_id, resolved_resume_id, question_count
    )
    questions = result.get("questions", []) if result.get("found") else []
    if not questions:
        raise RuntimeError("面试题生成失败，请稍后重试")

    session = InterviewSession(
        user_id=user_id,
        job_id=job_id,
        resume_id=resolved_resume_id,
        status="active",
    )
    db.add(session)
    await db.flush()

    for item in questions:
        db.add(
            InterviewQA(
                session_id=session.id,
                category=item.get("category", "technical"),
                question=item["question"],
            )
        )
    await db.commit()

    saved = await _get_owned_session(db, user_id, session.id)
    return await serialize_session(db, saved)


async def list_sessions(db: AsyncSession, user_id: int) -> list[dict]:
    """当前用户的面试会话列表（含答题进度与平均分）。"""
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == user_id)
        .options(_SESSION_LOAD)
        .order_by(InterviewSession.id.desc())
        .limit(20)
    )
    sessions = result.scalars().all()

    job_ids = {s.job_id for s in sessions if s.job_id}
    title_map: dict[int, str] = {}
    if job_ids:
        jobs = await db.execute(
            select(JobAnalysis).where(JobAnalysis.id.in_(job_ids))
        )
        for job in jobs.scalars().all():
            if job.parsed_json and job.parsed_json.get("position_title"):
                title_map[job.id] = job.parsed_json["position_title"]

    items: list[dict] = []
    for s in sessions:
        answered = [qa for qa in s.qas if qa.answer is not None]
        scores = [qa.score for qa in answered if qa.score is not None]
        items.append(
            {
                "id": s.id,
                "job_id": s.job_id,
                "position_title": title_map.get(s.job_id),
                "status": s.status,
                "created_at": s.created_at,
                "finished_at": s.finished_at,
                "qa_count": len(s.qas),
                "answered_count": len(answered),
                "average_score": round(sum(scores) / len(scores), 1)
                if scores
                else None,
            }
        )
    return items


async def get_session_detail(
    db: AsyncSession, user_id: int, session_id: int
) -> dict | None:
    session = await _get_owned_session(db, user_id, session_id)
    if not session:
        return None
    return await serialize_session(db, session)


async def _evaluate_answer(
    db: AsyncSession, session: InterviewSession, qa: InterviewQA, answer: str
) -> None:
    """调用 LLM 评估单轮回答并写回 qa（失败降级为中性评分，保证流程可用）。"""
    job_data = {}
    if session.job_id:
        job_data = await analyze_job_impl(db, session.job_id)

    # 多轮记忆：加载本轮之前的问答，让评估能结合上下文（需求 7.1）
    history_text = "（本场首轮，无历史对话）"
    history = [q for q in session.qas if q.answer is not None and q.id != qa.id]
    if history:
        lines = []
        for i, q in enumerate(history[-5:], 1):
            lines.append(f"第{i}轮 问：{q.question}\n第{i}轮 答：{q.answer[:500]}")
        history_text = "\n".join(lines)

    scores = {"logic": 60, "completeness": 60, "professionalism": 60}
    overall = 60
    strengths = weaknesses = suggestions = ""
    source = "llm"

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = get_chat_llm()
        resp = await llm.ainvoke(
            [
                SystemMessage(_EVAL_SYSTEM_PROMPT),
                HumanMessage(
                    f"【目标岗位】{job_data.get('position_title') or '未知岗位'}\n"
                    f"【岗位要求】\n"
                    f"{json.dumps(job_data.get('requirements', []), ensure_ascii=False)}\n\n"
                    f"【历史对话】\n{history_text}\n\n"
                    f"【本轮题目（{qa.category}）】\n{qa.question}\n\n"
                    f"【候选人回答】\n{answer[:_MAX_ANSWER_CHARS]}"
                ),
            ]
        )
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        raw = _extract_json(content)
        scores = {
            "logic": _clamp_score(raw.get("logic", 60)),
            "completeness": _clamp_score(raw.get("completeness", 60)),
            "professionalism": _clamp_score(raw.get("professionalism", 60)),
        }
        overall = _clamp_score(
            raw.get("overall")
            if raw.get("overall") is not None
            else round(sum(scores.values()) / 3)
        )
        strengths = str(raw.get("strengths") or "").strip()
        weaknesses = str(raw.get("weaknesses") or "").strip()
        suggestions = str(raw.get("suggestions") or "").strip()
        if not (strengths or weaknesses or suggestions):
            raise ValueError("评估内容为空")
    except Exception:
        logger.exception("LLM 评估回答失败，降级为中性评分")
        source = "fallback"
        strengths = "回答覆盖了问题的基本方面，表达完整。"
        weaknesses = "深度与细节不足，可能受限于当前作答长度。"
        suggestions = "建议用 STAR 结构补充具体场景、动作与量化结果。"

    qa.answer = answer
    qa.score = overall
    qa.feedback_json = {
        "scores": scores,
        "overall": overall,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "source": source,
    }
    qa.feedback = (
        f"【优点】{strengths}\n【不足】{weaknesses}\n【改进建议】{suggestions}"
    )


async def submit_answer(
    db: AsyncSession, user_id: int, session_id: int, qa_id: int, answer: str
) -> dict:
    """提交一轮回答：LLM 三维度评估 → 持久化 → 返回下一道待答题。"""
    session = await _get_owned_session(db, user_id, session_id)
    if not session:
        raise LookupError("面试会话不存在")
    if session.status != "active":
        raise ValueError("面试已结束，不能继续作答")

    qa = next((q for q in session.qas if q.id == qa_id), None)
    if not qa:
        raise LookupError("题目不存在")
    if qa.answer is not None:
        raise ValueError("该题已作答，不能重复提交")

    await _evaluate_answer(db, session, qa, answer.strip())
    await db.commit()

    # commit 后关系过期，重查后再找下一题（项目约定）
    saved = await _get_owned_session(db, user_id, session_id)
    answered_qa = next(q for q in saved.qas if q.id == qa_id)
    next_qa = next((q for q in saved.qas if q.answer is None), None)
    return {
        "qa": serialize_qa(answered_qa),
        "next_qa": serialize_qa(next_qa) if next_qa else None,
        "is_finished": next_qa is None,
    }


async def _build_fallback_summary(session: InterviewSession, answered: list) -> str:
    """LLM 总评失败时的规则化总评。"""
    scores = [qa.score for qa in answered if qa.score is not None]
    avg = round(sum(scores) / len(scores)) if scores else 0
    level = "表现良好" if avg >= 80 else "基本合格" if avg >= 60 else "需要重点提升"
    weak_points = [
        qa.feedback_json.get("weaknesses")
        for qa in answered
        if qa.feedback_json and qa.feedback_json.get("weaknesses")
    ]
    suggestion_points = [
        qa.feedback_json.get("suggestions")
        for qa in answered
        if qa.feedback_json and qa.feedback_json.get("suggestions")
    ]
    lines = [
        f"本场模拟面试共完成 {len(answered)} 轮，平均得分 {avg} 分，整体{level}。",
        "主要不足：" + "；".join(list(dict.fromkeys(weak_points))[:3]) + "。"
        if weak_points
        else "",
        "备考建议：" + "；".join(list(dict.fromkeys(suggestion_points))[:3]) + "。"
        if suggestion_points
        else "",
    ]
    return "\n".join(line for line in lines if line)


async def finish_session(
    db: AsyncSession, user_id: int, session_id: int
) -> dict:
    """结束面试并生成总评报告（需求 3.5 反馈报告）。"""
    session = await _get_owned_session(db, user_id, session_id)
    if not session:
        raise LookupError("面试会话不存在")

    answered = [qa for qa in session.qas if qa.answer is not None]
    if not answered:
        raise ValueError("还没有答题记录，无法生成面试报告")

    # 幂等：已结束的会话直接返回，不重复消耗 LLM
    if session.status == "finished" and session.summary:
        return await serialize_session(db, session)

    rounds = []
    for i, qa in enumerate(answered, 1):
        rounds.append(
            {
                "round": i,
                "category": qa.category,
                "question": qa.question,
                "answer": (qa.answer or "")[:_MAX_ANSWER_CHARS],
                "feedback_json": qa.feedback_json,
            }
        )

    summary = ""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = get_chat_llm()
        resp = await llm.ainvoke(
            [
                SystemMessage(_SUMMARY_SYSTEM_PROMPT),
                HumanMessage(
                    f"【目标岗位】{await _position_title(db, session.job_id) or '未知岗位'}\n"
                    f"【各轮问答与评分】\n{json.dumps(rounds, ensure_ascii=False, default=str)}"
                ),
            ]
        )
        summary = (
            resp.content if isinstance(resp.content, str) else str(resp.content)
        ).strip()
    except Exception:
        logger.exception("LLM 生成面试总评失败，降级为规则总评")

    if not summary:
        summary = await _build_fallback_summary(session, answered)

    session.status = "finished"
    session.finished_at = datetime.now(timezone.utc)
    session.summary = summary
    await db.commit()

    saved = await _get_owned_session(db, user_id, session_id)
    return await serialize_session(db, saved)
