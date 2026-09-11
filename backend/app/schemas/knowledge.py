"""知识库 / RAG 相关的 Pydantic 模型。"""

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class KnowledgeDocOut(ORMBase):
    """知识库文档列表项。"""

    id: int
    title: str
    file_type: str
    chunk_count: int


class KnowledgeDocDetail(KnowledgeDocOut):
    """文档详情（含原文内容）。"""

    content: str


class KnowledgeSearchRequest(BaseModel):
    """向量检索请求。"""

    query: str = Field(min_length=1, max_length=2000, description="查询文本")
    top_k: int | None = Field(default=None, ge=1, le=20, description="返回条数，默认读配置")
    threshold: float | None = Field(
        default=None, ge=0.0, le=1.0, description="最低相似度阈值，默认读配置"
    )


class KnowledgeSearchItem(BaseModel):
    """检索结果项。"""

    chunk_id: int
    doc_id: int
    doc_title: str
    content: str
    similarity: float


class KnowledgeAskRequest(BaseModel):
    """知识库问答请求。"""

    question: str = Field(min_length=1, max_length=2000, description="用户问题")
    top_k: int | None = Field(default=None, ge=1, le=20)


class KnowledgeSource(BaseModel):
    """回答引用来源。"""

    doc_id: int
    doc_title: str
    similarity: float


class KnowledgeAskResponse(BaseModel):
    """知识库问答响应（含来源引用）。"""

    answer: str
    sources: list[KnowledgeSource] = []
