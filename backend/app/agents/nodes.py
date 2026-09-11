"""Agent 节点实现：analyze → match → plan → output。

每个节点：
1. 调用对应 Tool（真实访问 DB / RAG / LLM）
2. 异常时不中断，记录到 state["errors"]（需求 6.3 降级处理）
3. 返回状态增量
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import CareerAgentState
from app.llm.client import get_chat_llm
from app.tools import (
    analyze_job_impl,
    knowledge_searcher,
    match_skills_impl,
    read_resume_impl,
)


def _summary_text(value) -> str:
    """把 dict/str/None 统一转成用于 prompt 的文本。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


async def node_analyze(state: CareerAgentState) -> dict:
    """分析节点：并行读取简历（resume_reader）与岗位要求（job_analyzer）。"""
    errors: list[str] = []
    resume: dict = {"found": False}
    job: dict = {"found": False}

    try:
        from app.core.database import async_session

        async with async_session() as db:
            resume, job = await read_resume_impl(db, state["user_id"]), await analyze_job_impl(
                db, state["job_id"]
            )
    except Exception as e:  # Tool 失败降级，不中断流程
        errors.append(f"analyze 节点失败: {e}")

    return {"resume": resume, "job": job, "errors": errors}


async def node_match(state: CareerAgentState) -> dict:
    """匹配节点：skill_matcher 计算匹配度，LLM 生成差距分析摘要。"""
    errors: list[str] = []
    match_result: dict = {}

    try:
        match_result = match_skills_impl(state["resume"], state["job"])
        if match_result.get("matched"):
            llm = get_chat_llm()
            resp = await llm.ainvoke(
                [
                    SystemMessage(
                        "你是资深职业规划顾问。基于给定的匹配数据和差距明细，"
                        "输出 3-5 句简明的匹配度分析（中文），指出核心优势与最需补齐的短板。"
                    ),
                    HumanMessage(
                        f"匹配数据：\n{_summary_text(match_result)}\n\n"
                        f"岗位：{_summary_text(state['job'].get('position_title'))}"
                    ),
                ]
            )
            match_result["analysis"] = (
                resp.content if isinstance(resp.content, str) else str(resp.content)
            )
    except Exception as e:
        errors.append(f"match 节点失败: {e}")
        match_result = {"matched": False}

    return {"match_result": match_result, "errors": errors}


async def node_plan(state: CareerAgentState) -> dict:
    """计划节点：knowledge_searcher 检索学习资源 + LLM 生成结构化学习计划。"""
    errors: list[str] = []
    knowledge: list[dict] = []
    plan: dict = {"tasks": []}

    job_title = state.get("job", {}).get("position_title") or "目标岗位"
    gaps = state.get("match_result", {}).get("gaps", [])
    query = f"{job_title} 学习路线 " + " ".join(g.get("skill_name", "") for g in gaps[:3])

    # 1. RAG 检索学习资源（降级：检索失败不阻塞计划生成）
    try:
        knowledge = await knowledge_searcher.ainvoke({"query": query, "top_k": 5})
    except Exception as e:
        errors.append(f"知识检索失败: {e}")

    # 2. LLM 生成结构化学习计划
    try:
        knowledge_text = (
            "\n".join(f"- [{k['doc_title']}] {k['content'][:200]}" for k in knowledge)
            if knowledge
            else "（知识库暂无相关资料，请基于通用最佳实践给出计划）"
        )
        llm = get_chat_llm()
        resp = await llm.ainvoke(
            [
                SystemMessage(
                    "你是学习规划师。根据差距分析为用户生成学习计划，必须输出 JSON，"
                    '格式：{"tasks": [{"task_name": "...", "description": "...", '
                    '"resource_url": "" 或 null, "priority": "high|medium|low", '
                    '"estimated_days": 3}]}，tasks 数量 3-6 个，按优先级排序，'
                    "优先补齐 high 优先级差距。仅输出 JSON，不要多余文字。"
                ),
                HumanMessage(
                    f"目标岗位：{job_title}\n差距分析：\n{_summary_text(gaps)}\n\n"
                    f"知识库参考资料：\n{knowledge_text}"
                ),
            ]
        )
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        plan = _extract_json(content)
    except Exception as e:
        errors.append(f"计划生成失败: {e}")

    return {"knowledge": knowledge, "plan": plan, "errors": errors}


def _extract_json(text: str) -> dict:
    """从 LLM 输出中容错提取 JSON 对象。"""
    text = text.strip()
    # 去掉 markdown 代码块
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {"tasks": []}
    except json.JSONDecodeError:
        return {"tasks": []}


async def node_output(state: CareerAgentState) -> dict:
    """输出节点：汇总所有节点结果，生成最终报告。"""
    match_result = state.get("match_result", {})
    plan = state.get("plan", {})
    knowledge = state.get("knowledge", [])
    errors = state.get("errors", [])

    if not match_result.get("matched"):
        report = {
            "success": False,
            "message": "无法完成匹配分析："
            + ("；".join(errors) if errors else "简历或岗位数据缺失"),
            "suggestion": "请先完成简历解析和岗位分析，再运行 Agent 工作流。",
        }
        return {"report": report}

    report = {
        "success": True,
        "position_title": state.get("job", {}).get("position_title"),
        "overall_score": match_result.get("overall_score", 0),
        "skill_match": match_result.get("skill_match", 0),
        "experience_match": match_result.get("experience_match", 0),
        "education_match": match_result.get("education_match", 0),
        "analysis": match_result.get("analysis", ""),
        "gaps": match_result.get("gaps", []),
        "plan": plan.get("tasks", []),
        "knowledge_sources": [
            {"doc_title": k["doc_title"], "similarity": k["similarity"]} for k in knowledge
        ],
        "errors": errors,
    }
    return {"report": report}
