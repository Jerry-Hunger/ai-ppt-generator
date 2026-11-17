from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 已知默认密钥：带着它们上生产等于鉴权形同虚设（可自签任意用户令牌）
_DEFAULT_JWT_SECRETS = {"dev-secret-change-me", "change-me-in-production"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI PPT Generator"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://aippt:aippt@localhost:39432/aippt"
    redis_url: str = "redis://localhost:39379/0"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"

    @model_validator(mode="after")
    def reject_default_jwt_secret_in_prod(self) -> "Settings":
        # 生产（debug=false）禁止使用默认密钥，启动即失败；开发环境放行便于本地跑通
        if not self.debug and self.jwt_secret in _DEFAULT_JWT_SECRETS:
            raise ValueError("生产环境必须配置非默认的 JWT_SECRET（openssl rand -hex 32 生成）")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
