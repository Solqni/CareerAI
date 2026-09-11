"""向量检索：pgvector 余弦距离 TopK 相似度检索。

检索流程：query 向量 → cosine_distance 排序 → 相似度阈值过滤 → 返回 TopK。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import DocumentChunk, KnowledgeDocument


async def search_similar_chunks(
    db: AsyncSession,
    query_vector: list[float],
    top_k: int | None = None,
    threshold: float | None = None,
) -> list[dict]:
    """按余弦相似度检索最相关的文档片段。

    Returns:
        [{"chunk_id", "doc_id", "doc_title", "content", "similarity"}]
        similarity = 1 - cosine_distance，范围 [0, 1]，越高越相似。
    """
    k = top_k or settings.RAG_TOP_K
    min_similarity = settings.RAG_SIMILARITY_THRESHOLD if threshold is None else threshold

    distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
    stmt = (
        select(DocumentChunk, KnowledgeDocument.title, distance)
        .join(KnowledgeDocument, DocumentChunk.doc_id == KnowledgeDocument.id)
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(distance)
        .limit(k)
    )
    rows = (await db.execute(stmt)).all()

    results: list[dict] = []
    for chunk, doc_title, dist in rows:
        similarity = 1.0 - float(dist)
        if similarity < min_similarity:
            continue
        results.append(
            {
                "chunk_id": chunk.id,
                "doc_id": chunk.doc_id,
                "doc_title": doc_title,
                "content": chunk.content,
                "similarity": round(similarity, 4),
            }
        )
    return results
