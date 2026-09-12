"""RAG 知识文档 AI 采集服务：给定主题 → LLM 生成结构化知识文档 → 切分向量化入库。

复用 rag.ingest_document 完整链路（解析→切分→向量化→knowledge_document/document_chunk），
文档标题加【AI采集】前缀便于与人工上传区分。
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import get_chat_llm
from app.services import rag

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "你是就业指导领域的知识库编辑。围绕给定主题撰写一篇结构化中文知识文档（Markdown 格式，"
    "1200-1800 字），用于大学生求职辅助系统的 RAG 知识库检索。要求：\n"
    "1. 内容真实、具体、可操作，分 3-5 个小节，多用条目列表；\n"
    "2. 贴近国内校园招聘实际，写具体技术栈、流程、话术、评分要点等；\n"
    "3. 直接输出 Markdown 正文，以一级标题开头，不要额外解释。"
)


async def collect_knowledge(
    db: AsyncSession, topic: str, doc_count: int = 1
) -> dict:
    """按主题生成 doc_count 篇知识文档并入库（RAG 链路复用）。"""
    from langchain_core.messages import HumanMessage

    llm = get_chat_llm()
    docs = []
    for i in range(doc_count):
        angle = ["核心知识梳理", "高频面试考察点与答题要点", "常见误区与备考建议"][i % 3]
        suffix = "" if doc_count == 1 else f"（{angle}）"
        content = None
        for attempt in range(2):  # LLM 偶发抖动重试一次
            try:
                resp = await llm.ainvoke(
                    [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": f"主题：「{topic}」{suffix}。请生成知识文档。"},
                    ]
                )
                candidate = resp.content if isinstance(resp.content, str) else str(resp.content)
                if len(candidate.strip()) >= 100:
                    content = candidate
                    break
            except Exception:
                logger.exception("AI 采集知识文档生成失败（第 %s 次）：%s", attempt + 1, topic)
        if content is None:
            continue

        title = f"【AI采集】{topic}{suffix}"[:255]
        doc = await rag.ingest_document(
            db, filename=f"{topic}.md", file_bytes=content.encode("utf-8"), title=title
        )
        docs.append({"id": doc.id, "title": doc.title, "chunk_count": doc.chunk_count})

    if not docs:
        raise RuntimeError("AI 采集知识文档失败，请稍后重试")
    return {"topic": topic, "documents": docs, "generated_count": len(docs)}
