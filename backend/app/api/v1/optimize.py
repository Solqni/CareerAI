"""简历优化 API（M4，需求 3.4）。

POST /api/v1/optimize：输入目标岗位（可选指定简历），Agent 结合岗位要求与简历内容
调用 LLM 生成结构化优化建议（关键词优化 / 经历量化 / 内容增强 / 结构建议）。
不新增数据表，建议作为独立接口返回（需求 4.1 无对应表）。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.optimize import OptimizeRequest, OptimizeResponse
from app.services.optimization import generate_optimization

router = APIRouter(prefix="/optimize", tags=["optimize"])


@router.post("", response_model=OptimizeResponse)
async def optimize_resume(
    payload: OptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成简历优化建议：关键词补充、经历量化、能力短板增强、结构建议。"""
    try:
        result = await generate_optimization(
            db, current_user.id, payload.job_id, payload.resume_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化建议生成失败：{e}")
    return result
