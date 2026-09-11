"""Embedding 向量化：调用百炼 text-embedding-v3（OpenAI 兼容接口）。

- 文档向量化（批量）与查询向量化分开封装
- 模型与维度从 config.py 读取（EMBEDDING_DIMENSIONS 默认 1024）
"""

from app.llm.client import get_embeddings


async def embed_documents(texts: list[str]) -> list[list[float]]:
    """批量向量化文档片段。"""
    if not texts:
        return []
    return await get_embeddings().aembed_documents(texts)


async def embed_query(text: str) -> list[float]:
    """向量化用户查询文本。"""
    return await get_embeddings().aembed_query(text)
