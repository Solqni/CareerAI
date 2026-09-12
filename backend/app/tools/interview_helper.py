"""interview_helper Tool：基于岗位要求（+ 用户简历）调用 LLM 生成面试题。

需求 3.5：根据岗位要求生成针对性面试题（技术题、项目题、行为题）。
需求 6.2 工具清单：generate_interview_q（LLM API，真实读取 DB 岗位/简历数据）。

导出：
- generate_interview_q_impl：异步实现（供 interview service 直接复用，传入业务 db session）
- generate_interview_q：@tool 包装版本（独立开 DB session，可被 LLM tool-calling 调用）
"""

import json
import logging
import re
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.llm.client import get_chat_llm
from app.models import JobAnalysis, Resume
from app.schemas.interview import GeneratedQuestion, InterviewCategory
from app.tools.job_analyzer import analyze_job_impl

logger = logging.getLogger(__name__)

_MAX_CONTEXT_CHARS = 6000

_CATEGORIES = [
    InterviewCategory.TECHNICAL,
    InterviewCategory.PROJECT,
    InterviewCategory.BEHAVIORAL,
]
_CATEGORY_LABEL = {
    "technical": "技术题（岗位核心技术栈、原理与实操）",
    "project": "项目题（结合简历中的项目经历深挖细节、难点与贡献）",
    "behavioral": "行为题（沟通协作、抗压、学习能力等软素质，可用 STAR 回答）",
}

_FALLBACK_QUESTIONS = {
    "technical": [
        "请介绍你对该岗位核心技术栈的理解，以及你在项目中是如何使用它的？",
        "请讲解一个你熟悉的技术原理，以及它在什么场景下能发挥作用？",
        "遇到过哪些棘手的技术问题？你是如何定位并解决的？",
    ],
    "project": [
        "请挑一个你最有代表性的项目，介绍背景、你的职责和最终成果。",
        "这个项目中最大的技术难点是什么？你做了哪些方案取舍？",
        "如果重做这个项目，你会在哪些地方做得不一样？",
    ],
    "behavioral": [
        "请讲一次你在高压或紧急 deadline 下完成任务的经历。",
        "与队友意见分歧时你是怎么处理的？请举一个具体例子。",
        "你平时如何学习一项新技术？请结合最近的例子说明。",
    ],
}


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


def _category_counts(total: int) -> list[tuple[InterviewCategory, int]]:
    """把总题数尽量均匀分配给三类（技术/项目/行为）。"""
    base, extra = total // 3, total % 3
    counts = [base + (1 if i < extra else 0) for i in range(3)]
    return list(zip(_CATEGORIES, counts))


async def _load_resume_for_job(
    db: AsyncSession, job: JobAnalysis, resume_id: Optional[int]
) -> Optional[Resume]:
    """加载简历：指定 ID 优先，否则取该岗位所属用户的最新简历。"""
    if resume_id:
        return await db.scalar(
            select(Resume)
            .where(Resume.id == resume_id)
            .where(Resume.user_id == job.user_id)
        )
    return await db.scalar(
        select(Resume)
        .where(Resume.user_id == job.user_id)
        .order_by(Resume.id.desc())
        .limit(1)
    )


def _fallback_questions(total: int) -> list[dict]:
    """LLM 不可用时的兜底题库（保证面试流程可演示）。"""
    result: list[dict] = []
    for category, count in _category_counts(total):
        pool = _FALLBACK_QUESTIONS[category.value]
        for i in range(count):
            result.append({"category": category.value, "question": pool[i % len(pool)]})
    return result


async def generate_interview_q_impl(
    db: AsyncSession,
    job_id: int,
    resume_id: Optional[int] = None,
    question_count: int = 6,
) -> dict:
    """生成面试题：读取岗位要求与简历 → LLM 生成三类题目 → Pydantic 校验。

    返回 {"found", "job_id", "position_title", "questions", "source"}。
    LLM 失败时降级为通用兜底题（source=fallback）。
    """
    job = await db.scalar(select(JobAnalysis).where(JobAnalysis.id == job_id))
    if not job:
        return {
            "found": False,
            "job_id": job_id,
            "position_title": None,
            "questions": [],
            "source": "none",
        }

    job_data = await analyze_job_impl(db, job_id)
    resume = await _load_resume_for_job(db, job, resume_id)
    resume_text = (resume.raw_text if resume else "") or ""
    resume_text = resume_text[:_MAX_CONTEXT_CHARS]

    # RAG 检索平台管理员知识库考点，作为技术题出题参考（失败降级不阻断）
    knowledge_text = "（知识库暂无相关内容）"
    try:
        from app.services.rag import search_knowledge

        skill_names = [
            str(r.get("skill_name"))
            for r in (job_data.get("requirements") or [])
            if isinstance(r, dict) and r.get("skill_name")
        ]
        query = " ".join([job_data.get("position_title") or "", *skill_names[:5]]).strip()
        hits = await search_knowledge(db, query, top_k=3) if query else []
        if hits:
            knowledge_text = "\n\n".join(
                f"[片段{i + 1}]（来源：{h['doc_title']}）\n{h['content']}"
                for i, h in enumerate(hits)
            )
    except Exception:
        logger.exception("面试出题知识库检索失败，忽略知识库参考")

    distribution = _category_counts(question_count)
    dist_text = "；".join(
        f"{_CATEGORY_LABEL[cat.value]} {n} 道" for cat, n in distribution if n > 0
    )

    questions: list[dict] = []
    source = "llm"
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = get_chat_llm()
        resp = await llm.ainvoke(
            [
                SystemMessage(
                    "你是资深技术面试官。根据目标岗位要求和用户简历生成针对性面试题，"
                    "必须输出 JSON，格式："
                    '{"questions": [{"category": "technical|project|behavioral", '
                    '"question": "面试题"}]}。要求：\n'
                    "1. 题目必须紧扣岗位要求中的技能/经验/学历，项目题必须基于简历真实项目；\n"
                    "2. 不得编造简历中不存在的经历；\n"
                    "3. 问题具体、开放、能考察深度，不要选择题/是非题；\n"
                    "4. 严格按指定的类别与数量输出；\n"
                    "5. 仅输出 JSON，不要多余文字。"
                ),
                HumanMessage(
                    f"【目标岗位】{job_data.get('position_title') or '未命名岗位'}\n"
                    f"【岗位要求】\n{json.dumps(job_data, ensure_ascii=False, default=str)}\n\n"
                    f"【用户简历摘要】\n{resume_text or '（未提供简历，项目题改为通用项目考察）'}\n\n"
                    f"【知识库参考（平台管理员知识库考点，技术题尽量结合考察）】\n{knowledge_text}\n\n"
                    f"【题目分配】{dist_text}，共 {question_count} 道"
                ),
            ]
        )
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        raw = _extract_json(content)
        for item in raw.get("questions", []):
            if not isinstance(item, dict):
                continue
            try:
                q = GeneratedQuestion(**item)
                questions.append(q.model_dump(mode="json"))
            except Exception:
                continue
    except Exception:
        logger.exception("LLM 生成面试题失败，降级为兜底题库")

    # 数量不足（LLM 异常或校验淘汰）时用兜底题补齐
    if len(questions) < question_count:
        fallback = _fallback_questions(question_count)
        existing = {q["question"] for q in questions}
        for q in fallback:
            if len(questions) >= question_count:
                break
            if q["question"] not in existing:
                questions.append(q)
        source = "fallback" if not questions else "llm+fallback"

    return {
        "found": True,
        "job_id": job_id,
        "position_title": job_data.get("position_title"),
        "questions": questions[:question_count],
        "source": source,
    }


@tool
async def generate_interview_q(job_id: int, question_count: int = 6) -> dict:
    """基于目标岗位要求调用 LLM 生成针对性面试题（技术题、项目题、行为题三类）。"""
    async with async_session() as db:
        return await generate_interview_q_impl(db, job_id, None, question_count)
