from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.audit.schemas import LoginLogItem, LoginLogPage, OperationLogItem, OperationLogPage
from app.modules.audit.service.log_service import log_service
from app.modules.user.schemas import UserProfile
from app.schemas.response import ApiResponse
from app.utils.response import success


router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/login-log/page", response_model=ApiResponse[LoginLogPage])
def get_login_log_page(
    page_num: int = Query(1, ge=1, alias="pageNum"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    username: str | None = None,
    ip_address: str | None = None,
    platform: str | None = None,
    event_type: int | None = None,
    trace_id: str | None = Query(None, min_length=32, max_length=32, pattern="^[0-9a-f]{32}$"),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_permission("audit_login.read")),
) -> ApiResponse[LoginLogPage]:
    """分页查询登录日志。"""
    rows, total = log_service.list_login_log_page(
        db,
        page_num,
        page_size,
        username=username.strip() if username else None,
        ip_address=ip_address.strip() if ip_address else None,
        platform=platform.strip() if platform else None,
        event_type=event_type,
        trace_id=trace_id,
        start_time=start_time,
        end_time=end_time,
    )
    return success(LoginLogPage(list=[LoginLogItem(**row) for row in rows], total=total))


@router.get("/operation-log/page", response_model=ApiResponse[OperationLogPage])
def get_operation_log_page(
    page_num: int = Query(1, ge=1, alias="pageNum"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    username: str | None = None,
    method: str | None = None,
    status_code: int | None = None,
    title: str | None = None,
    trace_id: str | None = Query(None, min_length=32, max_length=32, pattern="^[0-9a-f]{32}$"),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_permission("audit_operation.read")),
) -> ApiResponse[OperationLogPage]:
    """分页查询操作记录。"""
    rows, total = log_service.list_operation_log_page(
        db,
        page_num,
        page_size,
        username=username.strip() if username else None,
        method=method.strip() if method else None,
        status_code=status_code,
        title=title.strip() if title else None,
        trace_id=trace_id,
        start_time=start_time,
        end_time=end_time,
    )
    return success(OperationLogPage(list=[OperationLogItem(**row) for row in rows], total=total))
