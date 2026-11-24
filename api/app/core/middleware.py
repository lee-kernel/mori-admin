import time
import logging
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.modules.audit.service.log_service import log_service

logger = logging.getLogger("app")

# 不记录操作日志的路径前缀（静态资源、健康检查、日志查询自身等）。
_SKIP_PREFIXES = (
    f"{settings.API_PREFIX}/audit/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon",
)

# 只记录这些 HTTP 方法的操作（排除纯查看类的 GET 也可以，但为了完整审计先全记录）。
_RECORD_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}


def _extract_username(request: Request) -> tuple[int | None, str | None]:
    """从 Authorization 头解析当前用户 ID 和用户名。"""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None
    token = auth_header[7:]
    payload = decode_access_token(token)
    if not payload:
        return None, None
    username = payload.get("sub")
    user_id = payload.get("uid")
    if not username or not isinstance(user_id, int) or user_id <= 0:
        return None, None
    return user_id, username


class OperationLogMiddleware(BaseHTTPMiddleware):
    """记录所有 API 请求 到 operation_log 表的中间件。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 跳过不需要记录的路径
        path = request.url.path
        if any(path.startswith(prefix) for prefix in _SKIP_PREFIXES):
            return await call_next(request)

        # 只记录 API 路径下的请求
        if not path.startswith(f"{settings.API_PREFIX}/"):
            return await call_next(request)

        if request.method not in _RECORD_METHODS:
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        try:
            # 仅记录声明了 operation_log 依赖的请求
            title = getattr(request.state, "action_log_title", None)
            if title:
                user_id, username = _extract_username(request)
                db = SessionLocal()
                try:
                    log_service.create_operation_log(
                        db,
                        user_id=user_id,
                        username=username,
                        method=request.method,
                        url=path,
                        title=title,
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                        operated_at=datetime.now(timezone.utc),
                    )
                finally:
                    db.close()
        except Exception:
            # 日志记录失败不应影响正常请求
            logger.error("操作审计写入失败 | 阶段=保存审计记录")

        return response
