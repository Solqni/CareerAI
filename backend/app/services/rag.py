"""RAG 业务编排层：文档入库（解析→切分→向量化→存储）、检索、知识库问答。"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import get_chat_llm
from app.models import DocumentChunk, KnowledgeDocument
from app.rag.chunker import chunk_text
from app.rag.embedder import embed_documents, embed_query
from app.rag.retriever import search_similar_chunks
from app.services.file_extract import extract_text

ALLOWED_EXTS = (".pdf", ".docx", ".doc", ".md", ".txt")


async def ingest_document(
    db: AsyncSession,
    filename: str,
    file_bytes: bytes,
    title: str | None = None,
) -> KnowledgeDocument:
    """文档入库完整流程：提取文本 → 切分 → 向量化 → 写入 knowledge_document / document_chunk。"""
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_EXTS:
        raise ValueError(f"不支持的文件格式 {suffix}，仅支持 PDF/Word/Markdown/TXT")
    if len(file_bytes) > 20 * 1024 * 1024:
        raise ValueError("文件大小不能超过 20MB")

    raw_text = extract_text(filename, file_bytes)
    if not raw_text.strip():
        raise ValueError("无法从文件中提取文本内容")

    chunks = chunk_text(raw_text)
    if not chunks:
        raise ValueError("文档切分后无有效内容")

    # 批量向量化（真实调用 Embedding API）
    vectors = await embed_documents(chunks)

    doc = KnowledgeDocument(
        title=(title or filename.rsplit(".", 1)[0])[:255],
        file_type=suffix.lstrip("."),
        content=raw_text,
        chunk_count=len(chunks),
    )
    db.add(doc)
    await db.flush()

    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        db.add(
            DocumentChunk(
                doc_id=doc.id,
                chunk_index=idx,
                content=chunk,
                embedding=vector,  # list 自动转为 pgvector Vector
            )
        )

    await db.commit()
    await db.refresh(doc)
    return doc


async def list_documents(db: AsyncSession) -> list[KnowledgeDocument]:
    """获取知识库文档列表。"""
    rows = await db.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.id.desc()))
    return list(rows)


async def get_document(db: AsyncSession, doc_id: int) -> KnowledgeDocument | None:
    """获取文档详情。"""
    return await db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))


async def delete_document(db: AsyncSession, doc_id: int) -> bool:
    """删除文档及其所有 chunk（含向量）。"""
    doc = await get_document(db, doc_id)
    if not doc:
        return False
    await db.execute(delete(DocumentChunk).where(DocumentChunk.doc_id == doc_id))
    await db.execute(delete(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
    await db.commit()
    return True


async def search_knowledge(
    db: AsyncSession,
    query: str,
    top_k: int | None = None,
    threshold: float | None = None,
) -> list[dict]:
    """知识检索：查询向量化 → pgvector 余弦相似度检索。"""
    query_vector = await embed_query(query)
    return await search_similar_chunks(db, query_vector, top_k=top_k, threshold=threshold)


async def answer_question(db: AsyncSession, question: str, top_k: int | None = None) -> dict:
    """知识库问答：检索 TopK → 构建上下文 → LLM 生成回答（含来源引用）。"""
    hits = await search_knowledge(db, question, top_k=top_k)

    if not hits:
        return {
            "answer": "知识库中没有找到与该问题相关的内容，请先上传相关文档或换个问法。",
            "sources": [],
        }

    context = "\n\n".join(
        f"[片段{i + 1}]（来源：{h['doc_title']}，相似度 {h['similarity']}）\n{h['content']}"
        for i, h in enumerate(hits)
    )
    prompt = (
        "你是 CareerAI 求职助手。请仅依据以下知识库片段回答用户问题，"
        "不要编造片段之外的信息；若片段不足以回答，请明确说明。\n\n"
        f"知识库片段：\n{context}\n\n用户问题：{question}\n\n"
        "要求：用简洁的中文回答，并在末尾用一行列出引用的片段编号，如（引用：片段1、片段3）。"
    )

    llm = get_chat_llm()
    response = await llm.ainvoke(prompt)
    answer = response.content if isinstance(response.content, str) else str(response.content)

    sources = [
        {"doc_id": h["doc_id"], "doc_title": h["doc_title"], "similarity": h["similarity"]}
        for h in hits
    ]
    return {"answer": answer, "sources": sources}
