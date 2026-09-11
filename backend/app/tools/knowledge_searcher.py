"""knowledge_searcher Tool：在 RAG 知识库中检索岗位知识与学习资源（真实连接 pgvector）。"""

from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.services.rag import search_knowledge


async def search_knowledge_impl(
    db: AsyncSession, query: str, top_k: int | None = None
) -> list[dict]:
    """RAG 知识检索（复用 services.rag 的向量检索）。"""
    return await search_knowledge(db, query, top_k=top_k)


@tool
async def knowledge_searcher(query: str, top_k: int = 5) -> list[dict]:
    """在 RAG 知识库中检索与查询相关的知识与学习资源，返回片段列表（含来源与相似度）。"""
    async with async_session() as db:
        return await search_knowledge_impl(db, query, top_k=top_k)
