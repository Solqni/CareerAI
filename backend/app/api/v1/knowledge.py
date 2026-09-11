"""RAG 知识库接口：文档上传、管理、向量检索、知识库问答。

统一返回格式：{"code": 200, "data": ..., "message": "ok"}
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.response import fail, ok
from app.models import User
from app.schemas.knowledge import (
    KnowledgeAskRequest,
    KnowledgeDocDetail,
    KnowledgeDocOut,
    KnowledgeSearchRequest,
)
from app.services import rag

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传 PDF/Word/Markdown/TXT 文档，自动切分、向量化并入库。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    file_bytes = await file.read()
    try:
        doc = await rag.ingest_document(db, file.filename, file_bytes, title=title)
    except ValueError as e:
        return fail(str(e))

    return ok(
        KnowledgeDocOut.model_validate(doc).model_dump(),
        message=f"文档入库成功，切分为 {doc.chunk_count} 个片段",
    )


@router.get("/")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """知识库文档列表。"""
    docs = await rag.list_documents(db)
    return ok([KnowledgeDocOut.model_validate(d).model_dump() for d in docs])


@router.get("/{doc_id}")
async def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """文档详情（含原文内容）。"""
    doc = await rag.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return ok(KnowledgeDocDetail.model_validate(doc).model_dump())


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除文档及其向量切片。"""
    deleted = await rag.delete_document(db, doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="文档不存在")
    return ok(message="文档已删除")


@router.post("/search")
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """向量相似度检索：返回最相关的文档片段（TopK + 相似度阈值过滤）。"""
    try:
        hits = await rag.search_knowledge(
            db, payload.query, top_k=payload.top_k, threshold=payload.threshold
        )
    except Exception as e:
        return fail(f"检索失败：{e}", code=500)
    return ok(hits, message=f"命中 {len(hits)} 个片段")


@router.post("/ask")
async def ask_knowledge(
    payload: KnowledgeAskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """知识库问答：RAG 检索 + LLM 生成回答，返回答案与引用来源。"""
    try:
        result = await rag.answer_question(db, payload.question, top_k=payload.top_k)
    except Exception as e:
        return fail(f"问答失败：{e}", code=500)
    return ok(result)
