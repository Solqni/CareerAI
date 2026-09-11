"""LangGraph 工作流编排：analyze → match → plan → output 固定管线。

需求 6.1：使用 LangGraph 编排 Agent 工作流，支持多步骤任务的状态管理和流程控制。
"""

from langgraph.graph import END, StateGraph

from app.agents.nodes import node_analyze, node_match, node_output, node_plan
from app.agents.state import CareerAgentState


def build_career_graph():
    """构建职业成长 Agent 工作流图。"""
    graph = StateGraph(CareerAgentState)

    graph.add_node("analyze", node_analyze)
    graph.add_node("match", node_match)
    graph.add_node("plan", node_plan)
    graph.add_node("output", node_output)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "match")
    graph.add_edge("match", "plan")
    graph.add_edge("plan", "output")
    graph.add_edge("output", END)

    return graph.compile()


# 模块级单例（编译一次，复用执行）
career_graph = build_career_graph()
