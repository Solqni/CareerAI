"""CareerAgent 工作流状态定义（LangGraph StateGraph）。"""

import operator
from typing import Annotated, TypedDict


class CareerAgentState(TypedDict, total=False):
    """Agent 全局状态，在 analyze → match → plan → output 节点间流转。"""

    # 输入
    user_id: int
    job_id: int

    # 节点产出
    resume: dict  # resume_reader 结果（简历 + 技能 + 经历）
    job: dict  # job_analyzer 结果（岗位要求）
    match_result: dict  # skill_matcher 结果（总分 + 分项 + 差距）
    knowledge: list[dict]  # knowledge_searcher 结果（学习资源片段）
    plan: dict  # LLM 生成的学习计划（tasks 列表）
    report: dict  # 最终汇总报告

    # 异常收集（多节点累加，不覆盖）
    errors: Annotated[list[str], operator.add]
