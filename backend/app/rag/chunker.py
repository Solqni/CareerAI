"""文本切分：LangChain RecursiveCharacterTextSplitter。

参数（chunk_size / chunk_overlap）从 config.py 的 RAG 配置读取，
默认 800 / 80，符合需求文档 5.3 节建议值（500-1000 / 50-100）。
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


def get_splitter() -> RecursiveCharacterTextSplitter:
    """获取文本切分器实例。"""
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        # 中文友好的分隔符优先级：段落 → 换行 → 句子 → 标点
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        length_function=len,
    )


def chunk_text(text: str) -> list[str]:
    """将长文本切分为 chunk 列表，过滤空白片段。"""
    chunks = get_splitter().split_text(text)
    return [c.strip() for c in chunks if c.strip()]
