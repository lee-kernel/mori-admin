from typing import TypeVar

from app.schemas.response import ApiResponse


DataT = TypeVar("DataT")


def success(data: DataT | None = None, message: str = "success") -> ApiResponse[DataT]:
    """构造统一成功响应。"""
    return ApiResponse(data=data, message=message)
