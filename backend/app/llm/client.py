from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings


def get_chat_llm() -> ChatOpenAI:
    """获取 DeepSeek Chat LLM 实例（基于 OpenAI 兼容接口）。"""
    return ChatOpenAI(
        model=settings.DEEPSEEK_CHAT_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
        timeout=settings.LLM_TIMEOUT,
    )


def get_embeddings() -> OpenAIEmbeddings:
    """获取 DeepSeek Embedding 实例。"""
    return OpenAIEmbeddings(
        model=settings.DEEPSEEK_EMBEDDING_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )
