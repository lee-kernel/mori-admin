from typing import Generic, TypeVar

from pydantic import BaseModel


DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """接口统一响应结构，data 可按具体接口声明为不同类型。"""

    code: int = 200
    message: str = "success"
    data: DataT | None = None
