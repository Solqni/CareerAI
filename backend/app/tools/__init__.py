"""Tool Calling 工具集（真实连接 DB / RAG）。

- resume_reader: 读取用户简历结构化数据（DB）
- job_analyzer: 获取岗位分析结果与要求（DB）
- skill_matcher: 计算技能/经验/学历匹配度与差距（规则计算）
- knowledge_searcher: RAG 知识检索（pgvector）

每个工具同时导出：
- *_impl 异步实现函数（供 LangGraph 节点直接复用）
- @tool 包装版本（可被 LLM tool-calling 调用，独立开 DB session）
"""

from app.tools.job_analyzer import analyze_job_impl, job_analyzer
from app.tools.knowledge_searcher import knowledge_searcher, search_knowledge_impl
from app.tools.resume_reader import read_resume_impl, resume_reader
from app.tools.skill_matcher import match_skills_impl, skill_matcher

ALL_TOOLS = [resume_reader, job_analyzer, skill_matcher, knowledge_searcher]

__all__ = [
    "resume_reader",
    "read_resume_impl",
    "job_analyzer",
    "analyze_job_impl",
    "skill_matcher",
    "match_skills_impl",
    "knowledge_searcher",
    "search_knowledge_impl",
    "ALL_TOOLS",
]
