from fastapi import Depends, Request
from fastapi.params import Depends as DependsParam


def operation_log(title: str) -> DependsParam:
    """创建一个用于标记操作日志标题的 FastAPI 路由依赖。"""

    def mark_operation(request: Request) -> None:
        request.state.action_log_title = title

    return Depends(mark_operation)
