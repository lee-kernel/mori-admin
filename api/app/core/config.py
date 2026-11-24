from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import quote_plus

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict, SettingsError

from app.core.config_validation import ConfigurationError, validate_configuration


BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BASE_DIR


class Settings(BaseSettings):
    """环境变量优先于 api/.env。"""

    PROJECT_NAME: str = "Mori Admin API"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    PASSWORD_HASH_ITERATIONS: int = 260000
    LOGIN_MAX_FAILURES: int = Field(default=5, ge=1, le=100)
    LOGIN_LOCK_MINUTES: int = Field(default=15, ge=1, le=1440)
    TOTP_ISSUER: str = "Mori Admin"
    TOTP_ENCRYPTION_KEY: str = ""
    TOTP_CHALLENGE_EXPIRE_SECONDS: int = Field(default=300, ge=60, le=900)
    TOTP_SETUP_EXPIRE_SECONDS: int = Field(default=600, ge=60, le=1800)

    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:5173"])
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = BASE_DIR / "logs" / "app.audit"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5

    APP_TIMEZONE: str = "UTC"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "mori_admin"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "mori_admin"

    @property
    def DATABASE_URL(self) -> str:
        """拼接 SQLAlchemy 连接串，并编码账号密码中的特殊字符。"""
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    DATABASE_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_origin_list(cls, value: str | list[str] | None) -> list[str]:
        """支持在 .env 中用逗号分隔多个 Origin。"""
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        """统一检查配置语义，错误只包含字段名与固定说明。"""
        validate_configuration(self)
        return self

@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        errors = []
        for error in exc.errors(include_input=False, include_context=False, include_url=False):
            field = ".".join(str(part) for part in error["loc"]) or "配置"
            errors.append(f"{field}：类型或取值范围不正确")
        raise ConfigurationError(errors) from None
    except SettingsError:
        raise ConfigurationError(["配置：环境变量格式无法解析"]) from None


settings = get_settings()
