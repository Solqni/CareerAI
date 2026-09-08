from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

# PostgreSQL优化配置
if settings.DATABASE_TYPE == "sqlite":
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL连接池优化
    _engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,  # 自动检测断开的连接
        "pool_recycle": 3600,  # 1小时回收连接
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：获取数据库会话。"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库表（开发环境使用）。"""
    from app.models.base import Base
    from app.models import user, resume, job, match, interview, memory  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
