from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.config_validation import check_startup
from app.core.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.middleware import OperationLogMiddleware
from app.core.tracing import TraceIdMiddleware
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.modules.auth.api import router as auth_router
from app.modules.branding.api import router as branding_router
from app.modules.group.api import router as group_router
from app.modules.audit.api import router as log_router
from app.modules.menu.api import router as menu_router
from app.modules.user.api import router as user_router
from app.version import BUILD_VERSION


logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期钩子：启动时初始化基础表结构和默认数据。"""
    check_startup(settings)
    db = SessionLocal()
    try:
        logger.info("应用启动，开始初始化数据库结构和默认数据")
        init_db(db)
        logger.info("应用启动完成 | 环境=%s | API前缀=%s", settings.ENVIRONMENT, settings.API_PREFIX)
    finally:
        db.close()
    try:
        yield
    finally:
        logger.info("应用正在关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例，集中注册中间件、异常处理器和业务路由。"""
    configure_logging()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=BUILD_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.add_middleware(OperationLogMiddleware)
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Trace-Id"],
    )

    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(user_router, prefix=settings.API_PREFIX)
    app.include_router(group_router, prefix=settings.API_PREFIX)
    app.include_router(menu_router, prefix=settings.API_PREFIX)
    app.include_router(log_router, prefix=settings.API_PREFIX)
    app.include_router(branding_router, prefix=settings.API_PREFIX)

    @app.get("/healthz", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    # 便于本地调试直接执行 python -m app.main，Docker/生产环境仍建议使用 uvicorn 命令启动。
    uvicorn.run("app.main:app", host="127.0.0.1", port=9394, reload=True)
