import logging
import logging.config
from pathlib import Path

from app.core.config import settings
from app.core.config_validation import ConfigurationError


def exception_diagnostics(exc: BaseException) -> str:
    """返回异常链中的类型和数字错误码，不包含异常文本或请求数据。"""
    pending = [exc]
    seen = set()
    details = []
    while pending and len(details) < 8:
        current = pending.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        name = type(current).__name__
        code = getattr(current, "errno", None)
        details.append(f"{name}(errno={code})" if type(code) is int else name)
        pending.extend(item for item in (current.__cause__, current.__context__, *current.args) if isinstance(item, BaseException))
    return " -> ".join(details)


def configure_logging() -> None:
    """配置应用日志；不接管 uvicorn 日志，保留其默认启动和访问日志输出。"""
    log_file = Path(settings.LOG_FILE)
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8"):
            pass
    except OSError:
        raise ConfigurationError(["LOG_FILE：日志目录或文件不可写"]) from None

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | trace_id=%(trace_id)s | %(message)s",
                },
            },
            "filters": {"trace_id": {"()": "app.core.tracing.TraceIdFilter"}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["trace_id"],
                    "level": settings.LOG_LEVEL,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filters": ["trace_id"],
                    "filename": str(log_file),
                    "maxBytes": settings.LOG_MAX_BYTES,
                    "backupCount": settings.LOG_BACKUP_COUNT,
                    "encoding": "utf-8",
                    "level": settings.LOG_LEVEL,
                },
            },
            "loggers": {
                "app": {"handlers": ["console", "file"], "level": settings.LOG_LEVEL, "propagate": False},
            },
        }
    )
