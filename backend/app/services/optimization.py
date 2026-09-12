"""简历优化服务（M4，需求 3.4）。

Agent 根据目标岗位要求对用户简历生成结构化优化建议：
- 关键词优化（keyword）：识别简历缺少的 JD 关键词并建议补充
- 经历量化（quantify）：建议将描述性经历改为量化成果表达
- 内容增强（enhance）：针对能力短板建议补充项目经验或证书描述
- 结构建议（structure）：简历结构与排版建议

重要原则（需求 3.4）：不得编造用户未提供的经历或技能，所有建议基于真实简历内容。
实现：调用 LLM 传入简历与岗位要求，Pydantic 定义返回结构并校验（需求 8.3）。
不新增数据表，优化建议作为独立接口返回。
"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import get_chat_llm
from app.models import JobAnalysis, MatchReport, Resume
from app.schemas.optimize import OptimizationSuggestion
from app.tools.job_analyzer import analyze_job_impl

# 控制 Token 用量（需求 9.1），简历文本超出部分截断
_MAX_RESUME_CHARS = 6000

_OPTIMIZE_SYSTEM_PROMPT = (
    "你是资深简历优化顾问。根据目标岗位要求分析用户简历，生成结构化优化建议。"
    "必须输出 JSON，格式："
    '{"suggestions": [{"dimension": "keyword|quantify|enhance|structure", '
    '"issue": "问题定位", "suggestion": "具体修改建议", "example": "示例改法"}], '
    '"summary": "整体优化思路"}。\n'
    "要求：\n"
    "1. suggestions 4-8 条，覆盖 keyword/quantify/enhance/structure 四个维度；\n"
    "2. issue 必须定位到简历中的具体位置或明确缺失的内容；\n"
    "3. example 必须基于用户简历中已有的真实经历/技能改写，"
    "严禁编造用户未提供的经历、技能或数据；\n"
    "4. 仅输出 JSON，不要多余文字。"
)


def _extract_json(text: str) -> dict:
    """从 LLM 输出中容错提取 JSON 对象（与 agents/nodes.py 同策略）。"""
    import re

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


async def _load_resume(
    db: AsyncSession, user_id: int, resume_id: int | None
) -> Resume | None:
    """加载用户简历：指定 resume_id 或取最新一份，校验归属。"""
    if resume_id:
        return await db.scalar(
            select(Resume).where(Resume.id == resume_id).where(Resume.user_id == user_id)
        )
    return await db.scalar(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.id.desc())
        .limit(1)
    )


async def generate_optimization(
    db: AsyncSession, user_id: int, job_id: int, resume_id: int | None = None
) -> dict:
    """生成简历优化建议（M4 核心流程）。"""
    from langchain_core.messages import HumanMessage, SystemMessage

    # 1. 校验岗位可访问（自有或平台共享）并获取岗位要求（复用 job_analyzer）
    job = await db.scalar(
        select(JobAnalysis).where(JobAnalysis.id == job_id).where(
            or_(
                JobAnalysis.user_id == user_id,
                JobAnalysis.is_shared.is_(True),
            )
        )
    )
    if not job:
        raise ValueError("岗位不存在或无权访问")

    # 2. 校验简历存在
    resume = await _load_resume(db, user_id, resume_id)
    if not resume:
        raise ValueError("未找到简历，请先上传并解析简历")

    job_data = await analyze_job_impl(db, job_id)

    # 3. 取最近一次人岗匹配的能力差距清单，作为优化上下文（需求 3.4：结合能力差距分析）
    report = await db.scalar(
        select(MatchReport)
        .where(MatchReport.user_id == user_id)
        .where(MatchReport.job_id == job_id)
        .order_by(MatchReport.analyzed_at.desc())
        .limit(1)
    )
    if report and report.gaps_json:
        gap_text = json.dumps(report.gaps_json, ensure_ascii=False)
        report_id = report.id
        gap_skills = [
            str(g.get("skill_name"))
            for g in report.gaps_json
            if isinstance(g, dict) and g.get("skill_name")
        ]
    else:
        gap_text = "（该岗位尚无匹配报告，请基于简历与岗位要求直接识别能力差距）"
        report_id = None
        gap_skills = []

    # 3.5 RAG 检索管理员知识库片段作为优化参考（失败降级不阻断主流程）
    from app.services.rag import search_knowledge

    knowledge_refs: list[dict] = []
    knowledge_text = "（知识库暂无相关内容）"
    try:
        query = " ".join(
            [job_data.get("position_title") or "", *gap_skills[:5]]
        ).strip()
        if query:
            hits = await search_knowledge(db, query, top_k=4)
        else:
            hits = []
        if hits:
            knowledge_refs = [
                {
                    "doc_id": h["doc_id"],
                    "doc_title": h["doc_title"],
                    "similarity": h["similarity"],
                }
                for h in hits
            ]
            knowledge_text = "\n\n".join(
                f"[片段{i + 1}]（来源：{h['doc_title']}）\n{h['content']}"
                for i, h in enumerate(hits)
            )
    except Exception:
        import logging

        logging.getLogger(__name__).exception("优化建议知识库检索失败，忽略知识库参考")

    # 4. LLM 生成结构化优化建议
    llm = get_chat_llm()
    resume_text = (resume.raw_text or "")[:_MAX_RESUME_CHARS]
    resp = await llm.ainvoke(
        [
            SystemMessage(_OPTIMIZE_SYSTEM_PROMPT),
            HumanMessage(
                f"【用户简历】\n{resume_text or '（简历文本缺失，仅有结构化解析结果）'}\n\n"
                f"【目标岗位】{job_data.get('position_title') or '未命名岗位'}\n"
                f"【岗位要求】\n{json.dumps(job_data, ensure_ascii=False, default=str)}\n\n"
                f"【能力差距分析（最近匹配报告 {report_id or '：无'}）】\n{gap_text}"
            ),
        ]
    )
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    raw = _extract_json(content)

    # 5. Pydantic 校验（需求 8.3 结构化输出），非法条目丢弃
    suggestions: list[dict] = []
    for item in raw.get("suggestions", []):
        try:
            suggestions.append(OptimizationSuggestion(**item).model_dump(mode="json"))
        except Exception:
            continue

    return {
        "job_id": job_id,
        "position_title": job_data.get("position_title"),
        "resume_id": resume.id,
        "suggestions": suggestions,
        "summary": raw.get("summary"),
        "knowledge_refs": knowledge_refs,
    }
