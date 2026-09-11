"""Agent 智能体接口：触发完整工作流 / 对话式交互（多轮记忆）。

统一返回格式：{"code": 200, "data": ..., "message": "ok"}
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.response import fail, ok
from app.models import User
from app.schemas.agent import AgentChatRequest, AgentRunRequest
from app.schemas.agent import AgentChatResponse, AgentReportOut
from app.services import agent_service

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run")
async def run_agent(
    payload: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """触发完整 Agent 工作流：analyze → match → plan → output。

    输入 user_id + job_id，自动读取简历与岗位 → 计算匹配 → RAG 检索学习资源
    → 生成学习计划，结果持久化到 match_report / gap_item / learning_plan。
    """
    try:
        result = await agent_service.run_career_agent(db, payload.user_id, payload.job_id)
    except Exception as e:
        return fail(f"Agent 执行失败：{e}", code=500)

    report = AgentReportOut.model_validate(result["report"]).model_dump()
    return ok(
        {"report": report, "report_id": result["report_id"], "plan_id": result["plan_id"]},
        message="Agent 工作流执行完成" if result["report"] else "Agent 执行未产出结果",
    )


@router.post("/chat")
async def chat_agent(
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Agent 对话：支持多轮上下文（短期记忆），按需调用简历/岗位/知识库工具。"""
    if not payload.message.strip():
        return fail("消息不能为空")

    try:
        result = await agent_service.build_context_with_tools(
            db, current_user.id, payload.conversation_id, payload.message.strip()
        )
    except Exception as e:
        return fail(f"对话处理失败：{e}", code=500)

    return ok(AgentChatResponse.model_validate(result).model_dump())
