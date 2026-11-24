"""启动配置检查；诊断只包含字段名与固定说明，禁止拼接原始值。"""

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

if TYPE_CHECKING:
    from app.core.config import Settings


class ConfigurationError(RuntimeError):
    """可安全输出的配置错误清单。"""

    def __init__(self, errors: list[str]):
        super().__init__("启动配置检查失败：\n" + "\n".join(f"- {item}" for item in errors))


def _http_url(value: str, *, origin: bool = False) -> bool:
    try:
        parsed = urlsplit(value)
        return bool(
            parsed.scheme in ("http", "https") and parsed.hostname
            and parsed.port != 0 and not parsed.username and not parsed.password
            and not parsed.query and not parsed.fragment
            and (not origin or parsed.path in ("", "/"))
        )
    except ValueError:
        return False


def validate_configuration(config: "Settings") -> None:
    """检查应用和数据库配置。"""
    errors = []

    def require(condition: bool, field: str, message: str) -> None:
        if not condition:
            errors.append(f"{field}：{message}")

    require(len(config.SECRET_KEY.strip()) >= 32,
            "SECRET_KEY", "请设置至少 32 个字符的随机密钥")
    if config.TOTP_ENCRYPTION_KEY.strip():
        try:
            from cryptography.fernet import Fernet

            Fernet(config.TOTP_ENCRYPTION_KEY.strip().encode("ascii"))
        except Exception:
            errors.append("TOTP_ENCRYPTION_KEY：不是有效的 Fernet 密钥")
    require(config.ENVIRONMENT != "production" or not config.DEBUG, "DEBUG", "生产环境必须关闭调试")
    require(all(_http_url(origin, origin=True) and not origin.endswith("/")
                for origin in config.BACKEND_CORS_ORIGINS),
            "BACKEND_CORS_ORIGINS", "必须是无路径的 HTTP Origin 列表")
    require(config.PASSWORD_HASH_ITERATIONS >= 260000,
            "PASSWORD_HASH_ITERATIONS", "至少为 260000")
    for field in ("POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_DB", "POSTGRES_PASSWORD"):
        require(bool(getattr(config, field).strip()), field, "不能为空")
    for field, minimum, maximum in (
        ("POSTGRES_PORT", 1, 65535), ("DB_POOL_SIZE", 1, None),
        ("DB_MAX_OVERFLOW", 0, None), ("DB_POOL_RECYCLE", 1, None),
        ("LOG_MAX_BYTES", 1, None), ("LOG_BACKUP_COUNT", 1, None),
        ("ACCESS_TOKEN_EXPIRE_MINUTES", 1, None), ("PASSWORD_HASH_ITERATIONS", 1, None),
    ):
        value = getattr(config, field)
        require(value >= minimum and (maximum is None or value <= maximum), field, "超出允许范围")
    try:
        ZoneInfo(config.APP_TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        errors.append("APP_TIMEZONE：不是有效的 IANA 时区")
    require(config.LOG_LEVEL in logging.getLevelNamesMapping(), "LOG_LEVEL", "不是有效的日志级别")
    if errors:
        raise ConfigurationError(errors)


def check_connections(config: "Settings") -> None:
    """只读探测 PostgreSQL；连接与语句超时各为 5 秒，不初始化数据库。"""
    import psycopg

    try:
        with psycopg.connect(
            host=config.POSTGRES_HOST, port=config.POSTGRES_PORT,
            user=config.POSTGRES_USER, password=config.POSTGRES_PASSWORD,
            dbname=config.POSTGRES_DB, connect_timeout=5,
            options="-c statement_timeout=5000 -c default_transaction_read_only=on",
        ) as connection:
            connection.execute("SELECT 1")
    except Exception:
        raise ConfigurationError(["PostgreSQL：连接检查失败，请检查地址、凭据及数据库状态"]) from None


def check_startup(config: "Settings") -> None:
    """检查启动所需的静态配置与数据库，不装配日志或任务。"""
    validate_configuration(config)
    check_connections(config)
