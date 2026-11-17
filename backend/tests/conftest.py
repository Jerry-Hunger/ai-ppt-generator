import os

# 1. 环境变量优先级高于 .env：测试固定关掉 SQL echo，并使用独立长密钥
#    （既消除 pyjwt 短密钥警告，也不受本地 .env 是否换过密钥影响）
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("JWT_SECRET", "test-only-secret-" + "x" * 48)

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import get_session  # noqa: E402
from app.main import app  # noqa: E402

# 2. 测试专用引擎：TestClient 每个请求跑在独立事件循环上，
#    NullPool 关闭连接复用，避免 asyncpg 连接跨事件循环复用报错
db_engine = create_async_engine(settings.database_url, poolclass=NullPool)
db_session_factory = async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def override_get_session():
    async def _override() -> AsyncGenerator[AsyncSession]:
        async with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.pop(get_session, None)
