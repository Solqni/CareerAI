"""简历优化（M4）Pydantic 模型。

需求 3.4：LLM 返回结构化优化建议列表，每条含问题定位 + 具体修改建议 + 示例改法；
重要原则：不得编造用户未提供的经历或技能，所有建议基于用户真实简历信息。
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class OptimizeDimension(str, Enum):
    """优化维度（需求 3.4）"""
    KEYWORD = "keyword"  # 关键词优化：补充目标岗位 JD 关键词
    QUANTIFY = "quantify"  # 经历量化建议：描述性经历改为量化成果
    ENHANCE = "enhance"  # 内容增强：针对能力短板补充项目/证书描述
    STRUCTURE = "structure"  # 简历结构建议


class OptimizeRequest(BaseModel):
    """简历优化请求"""
    job_id: int = Field(..., description="目标岗位ID（已解析的 job_analysis）")
    resume_id: Optional[int] = Field(None, description="简历ID，缺省取用户最新简历")
    refresh: bool = Field(False, description="True 时忽略缓存强制重新生成")


class OptimizationSuggestion(BaseModel):
    """单条优化建议"""
    dimension: OptimizeDimension = Field(..., description="优化维度")
    issue: str = Field(..., description="问题定位：指出简历中的具体问题位置或缺失内容")
    suggestion: str = Field(..., description="具体修改建议")
    example: Optional[str] = Field(None, description="示例改法（基于用户真实信息的改写示例）")


class KnowledgeRef(BaseModel):
    """知识库引用来源（来自平台管理员知识库）"""
    doc_id: int = Field(..., description="知识文档ID")
    doc_title: str = Field(..., description="知识文档标题")
    similarity: float = Field(..., description="与岗位/差距的相似度")


class OptimizeResponse(BaseModel):
    """简历优化结果"""
    job_id: int
    position_title: Optional[str] = None
    resume_id: Optional[int] = None
    suggestions: List[OptimizationSuggestion] = Field(default_factory=list)
    summary: Optional[str] = Field(None, description="整体优化思路概述")
    knowledge_refs: List[KnowledgeRef] = Field(
        default_factory=list, description="RAG 检索引用的知识库来源"
    )
    source: str = Field("llm", description="llm=新生成；cache=历史报告缓存")
    created_at: Optional[str] = Field(None, description="报告生成时间（缓存时为首次生成时间）")
