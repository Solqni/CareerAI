from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动 / 关闭生命周期。"""
    if settings.APP_ENV != "testing":
        await init_db()
    yield


app = FastAPI(
    title="CareerAI API",
    description="AI求职与职业成长智能体 - 后端接口",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "careerai-backend"}


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "CareerAI API running", "docs": "/docs"}
