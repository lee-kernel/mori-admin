from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status


def _error_response(message: str, code: int, data=None) -> JSONResponse:
    """构造统一错误响应，HTTP 状态码与业务 code 一致。"""
    return JSONResponse(
        status_code=code,
        content={"code": code, "message": message, "data": data},
    )


def http_exception_handler(request: Request, exc: HTTPException):
    """将主动抛出的 HTTPException 转换为统一响应格式。"""
    return _error_response(str(exc.detail), code=exc.status_code)


def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求参数校验失败，并返回具体校验错误。"""
    return _error_response(
        "Request validation failed",
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        data=exc.errors(),
    )


def unhandled_exception_handler(request: Request, exc: Exception):
    """兜底处理未捕获异常，避免内部错误直接暴露给客户端。"""
    return _error_response(
        "Internal server error",
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
