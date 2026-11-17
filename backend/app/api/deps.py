from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User

# auto_error=False：缺头时不让 FastAPI 自动返回 403，统一由下方抛 401
bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: SessionDep,
) -> User:
    # 1. 缺少 Authorization: Bearer 头
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "缺少访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 2. 令牌签名无效或已过期
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        # 无效令牌是预期内的客户端错误，主动抑制异常链避免污染 500 堆栈
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "无效或过期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    # 3. 令牌有效但用户已被删除
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
