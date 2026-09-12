from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.agent import router as agent_router
from app.api.v1.auth import router as auth_router
from app.api.v1.interview import router as interview_router
from app.api.v1.job import router as job_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.match import router as match_router
from app.api.v1.optimize import router as optimize_router
from app.api.v1.resume import router as resume_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(resume_router)
api_router.include_router(job_router)
api_router.include_router(match_router)
api_router.include_router(interview_router)
api_router.include_router(knowledge_router)
api_router.include_router(agent_router)
api_router.include_router(optimize_router)
api_router.include_router(admin_router)
