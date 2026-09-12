"""面试准备 API（M5，需求 3.5）。

- POST   /interview/questions           仅生成面试题（技术/项目/行为三类）
- POST   /interview/session             创建模拟面试会话（同时生成题库）
- GET    /interview/sessions            当前用户的会话列表
- GET    /interview/session/{id}        会话详情（含全部问答与评估）
- POST   /interview/session/{id}/answer 提交一轮回答，返回三维度评估与下一题
- POST   /interview/session/{id}/finish 结束面试，生成总评报告
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.interview import (
    AnswerResult,
    AnswerSubmit,
    InterviewCreate,
    QuestionBankResponse,
    QuestionGenerateRequest,
    SessionListItem,
    SessionOut,
)
from app.services import interview as interview_service

router = APIRouter(prefix="/interview", tags=["interview"])
logger = logging.getLogger(__name__)


@router.post("/questions", response_model=QuestionBankResponse)
async def generate_questions(
    payload: QuestionGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """根据岗位要求（+ 简历）调用 LLM 生成技术/项目/行为面试题。"""
    try:
        return await interview_service.generate_questions(
            db,
            current_user.id,
            payload.job_id,
            payload.resume_id,
            payload.question_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("面试题生成失败")
        raise HTTPException(status_code=500, detail=f"面试题生成失败：{e}")


@router.post("/session", response_model=SessionOut, status_code=201)
async def create_session(
    payload: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建模拟面试会话：生成题库并返回首轮题目。"""
    try:
        return await interview_service.create_session(
            db,
            current_user.id,
            payload.job_id,
            payload.resume_id,
            payload.question_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("创建面试会话失败")
        raise HTTPException(status_code=500, detail=f"创建面试会话失败：{e}")


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的面试会话历史。"""
    return await interview_service.list_sessions(db, current_user.id)


@router.get("/session/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取面试会话详情（含全部问答、逐轮评估与总评）。"""
    session = await interview_service.get_session_detail(
        db, current_user.id, session_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    return session


@router.post("/session/{session_id}/answer", response_model=AnswerResult)
async def submit_answer(
    session_id: int,
    payload: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交一轮回答：LLM 从逻辑性/完整性/专业性评估，返回评估结果与下一题。"""
    try:
        return await interview_service.submit_answer(
            db, current_user.id, session_id, payload.qa_id, payload.answer
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("答案评估失败")
        raise HTTPException(status_code=500, detail=f"答案评估失败：{e}")


@router.post("/session/{session_id}/finish", response_model=SessionOut)
async def finish_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """结束面试并生成总评报告（优点/不足/备考建议汇总）。"""
    try:
        return await interview_service.finish_session(db, current_user.id, session_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("生成面试总评失败")
        raise HTTPException(status_code=500, detail=f"生成面试总评失败：{e}")
