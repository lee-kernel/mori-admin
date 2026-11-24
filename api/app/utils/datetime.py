from datetime import date, datetime, timezone
from typing import Any


def to_utc_datetime(value: datetime) -> datetime:
    """将时间归一为 UTC-aware ``datetime``；无时区值按 UTC 兼容解释。"""
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return aware.astimezone(timezone.utc)


def to_iso_string(value: Any) -> str | None:
    """将数据库日期时间转换为稳定的 ISO 字符串。

    数据库连接统一使用 UTC；兼容处理驱动或测试替身返回的不带时区 ``datetime``，按 UTC
    解释；纯日期保持不变。
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return to_utc_datetime(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)
