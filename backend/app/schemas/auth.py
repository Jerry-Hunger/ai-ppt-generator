from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field


def _within_bcrypt_limit(v: str) -> str:
    # 1. bcrypt 5.0 对超过 72 字节的输入直接抛 ValueError（中文每字占 3 字节），在 schema 层统一拦截
    if len(v.encode("utf-8")) > 72:
        raise ValueError("密码长度不能超过 72 字节")
    return v


# 注册与登录共用同一密码约束，避免登录路径漏掉上限校验后被超长输入打成 500
PasswordStr = Annotated[str, Field(min_length=8), AfterValidator(_within_bcrypt_limit)]
# 邮箱/用户名大小写不敏感：入库与查询前统一转小写，防止大小写变体重复注册、登录大小写不匹配
EmailLowerStr = Annotated[EmailStr, AfterValidator(str.lower)]
UsernameLowerStr = Annotated[str, Field(min_length=2, max_length=50), AfterValidator(str.lower)]


class UserCreate(BaseModel):
    email: EmailLowerStr
    username: UsernameLowerStr
    password: PasswordStr


class LoginRequest(BaseModel):
    email: EmailLowerStr
    password: PasswordStr


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
