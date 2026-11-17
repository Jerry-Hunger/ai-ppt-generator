from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

# 1. 密码哈希：项目仅安装了 bcrypt 后端，显式指定避免 pwdlib 回退到不可用的 argon2
password_hash = PasswordHash((BcryptHasher(),))

# 2. 固定哑哈希：登录时用户不存在也执行一次同代价的 bcrypt 校验，
#    消除「存在/不存在」账号的响应时间差（防账号枚举）；预生成字面量避免启动耗时
DUMMY_PASSWORD_HASH = "$2b$12$vO0k0ULLmqJnD63E1fkqy.W83oHU9CdRPpIYGpOsVfDFEeSAhiEuq"


def hash_password(plain: str) -> str:
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    # 1. claims 只放最小必要信息：sub（用户 id）+ 签发/过期时间，角色等后续按需加
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """解码并校验 JWT（签名/过期/sub 格式），返回用户 id；无效时抛 jwt.PyJWTError，由调用方转 401"""
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    # 1. 签名有效但 sub 缺失/非数字（如与其他服务共用密钥的令牌）：归一为无效令牌而非 500
    sub = payload.get("sub")
    if sub is None or not str(sub).isdigit():
        raise jwt.InvalidTokenError("令牌缺少有效的用户标识")
    return int(sub)
