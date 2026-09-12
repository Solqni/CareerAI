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


def get_vision_llm() -> ChatOpenAI:
    """获取视觉 LLM 实例（识别 JD 截图等图片，走同一 OpenAI 兼容端点）。

    vl_high_resolution_images=True：DashScope qwen-vl 专属参数，
    对长图/密集小字截图保留原始分辨率，避免默认缩图丢字。
    """
    return ChatOpenAI(
        model=settings.DEEPSEEK_VISION_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=0,
        timeout=settings.LLM_TIMEOUT,
        max_retries=1,
        extra_body={"vl_high_resolution_images": True},
    )


def get_embeddings() -> OpenAIEmbeddings:
    """获取百炼文本向量模型实例（text-embedding-v3，OpenAI 兼容接口）。

    check_embedding_ctx_length=False：禁用本地 tiktoken 分词，
    直接传原始字符串给 API（百炼不接受 token 数组输入）。
    """
    return OpenAIEmbeddings(
        model=settings.DEEPSEEK_EMBEDDING_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        dimensions=settings.EMBEDDING_DIMENSIONS,
        timeout=settings.LLM_TIMEOUT,
        check_embedding_ctx_length=False,
    )
