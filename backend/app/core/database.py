from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 1. 异步引擎：pool_pre_ping 防止长连接被 PG 断开后拿到死连接
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# 2. 会话工厂：expire_on_commit=False 让 commit 后对象仍可访问（配合 Pydantic 序列化）
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 SQLAlchemy 模型的声明基类，Alembic autogenerate 依赖它的 metadata"""


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI 依赖项：每请求一个会话，请求结束自动关闭"""
    async with async_session_maker() as session:
        yield session
