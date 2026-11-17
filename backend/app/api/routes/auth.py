from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, SessionDep
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: SessionDep) -> User:
    # 1. 唯一性预检：单次查询覆盖邮箱+用户名，按命中列区分提示；并发冲突由 DB 唯一约束兜底
    dup = await session.scalar(
        select(User).where(
            or_(User.email == payload.email, User.username == payload.username)
        )
    )
    if dup:
        field = "邮箱" if dup.email == payload.email else "用户名"
        raise HTTPException(status.HTTP_409_CONFLICT, f"该{field}已被注册")

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        # 2. 预检与提交之间的竞态窗口：回滚后返回统一冲突信息
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "该邮箱或用户名已被注册") from None
    # 3. refresh 取回 server_default 生成的 created_at
    await session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == payload.email))
    # 1. 用户不存在时对哑哈希执行同代价校验，消除响应时间差导致的账号枚举
    password_ok = verify_password(
        payload.password, user.password_hash if user else DUMMY_PASSWORD_HASH
    )
    # 2. 两种失败返回同一提示，不暴露账号是否存在
    if user is None or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "邮箱或密码错误")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
async def read_current_user(user: CurrentUser) -> User:
    return user
