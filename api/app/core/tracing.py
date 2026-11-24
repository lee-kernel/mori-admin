import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse

trace_id_context: ContextVar[str] = ContextVar("trace_id", default="-")
logger = logging.getLogger("app")


def current_trace_id() -> str | None:
    """返回当前请求或任务标识；无上下文时返回 None。"""
    value = trace_id_context.get()
    return None if value == "-" else value


@contextmanager
def new_trace():
    """为一次后台执行创建隔离上下文，并在结束后恢复原上下文。"""
    trace_id = uuid4().hex
    token = trace_id_context.set(trace_id)
    try:
        yield trace_id
    finally:
        trace_id_context.reset(token)


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_context.get()
        return True


class TraceIdMiddleware:
    """为每个 HTTP 请求生成服务端标识，并关联应用日志与响应头。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        trace_id = uuid4().hex
        token = trace_id_context.set(trace_id)
        started = time.perf_counter()
        status = 500
        response_started = False

        async def send_with_trace(message):
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                MutableHeaders(scope=message)["X-Trace-Id"] = trace_id
            await send(message)

        try:
            try:
                await self.app(scope, receive, send_with_trace)
            except Exception:
                logger.exception("请求发生未处理异常")
                if response_started:
                    raise
                response = JSONResponse(
                    {"code": 500, "message": "Internal server error", "data": None},
                    status_code=500,
                )
                await response(scope, receive, send_with_trace)
            finally:
                logger.info(
                    "HTTP 请求 | 方法=%s | 路径=%s | 状态=%s | 耗时毫秒=%s",
                    scope["method"], getattr(scope.get("route"), "path", "<未匹配>"), status,
                    round((time.perf_counter() - started) * 1000),
                )
        finally:
            trace_id_context.reset(token)
