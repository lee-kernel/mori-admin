from datetime import datetime

from pydantic import BaseModel


class LoginLogItem(BaseModel):
    """登录日志条目。"""

    id: int
    trace_id: str | None = None
    user_id: int | None = None
    username: str | None = None
    ip_address: str | None = None
    platform: str | None = None
    browser: str | None = None
    event_type: int = 1
    login_at: str | None = None


class LoginLogPage(BaseModel):
    """登录日志分页响应。"""

    list: list[LoginLogItem]
    total: int


class LoginLogQuery(BaseModel):
    """登录日志查询参数。"""

    username: str | None = None
    ip_address: str | None = None
    platform: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class OperationLogItem(BaseModel):
    """操作记录条目。"""

    id: int
    trace_id: str | None = None
    user_id: int | None = None
    username: str | None = None
    method: str | None = None
    url: str | None = None
    title: str | None = None
    status_code: int = 0
    duration_ms: int = 0
    operated_at: str | None = None


class OperationLogPage(BaseModel):
    """操作记录分页响应。"""

    list: list[OperationLogItem]
    total: int


class OperationLogQuery(BaseModel):
    """操作记录查询参数。"""

    username: str | None = None
    method: str | None = None
    status_code: int | None = None
    title: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
