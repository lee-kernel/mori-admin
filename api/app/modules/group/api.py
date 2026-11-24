from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.decorators import operation_log
from app.db.session import get_db

from app.modules.auth.dependencies import require_admin_permission, require_any_permission, require_permission
from app.modules.group.schemas import (
    GroupCreate,
    GroupOptions,
    GroupPage,
    GroupProfile,
    GroupUpdate,
)
from app.modules.group.service.group_service import group_service
from app.modules.menu.service.menu_service import menu_service
from app.modules.user.schemas import UserProfile
from app.modules.access_control.catalog import DOMAIN_LABELS, OPERATION_LABELS, PERMISSIONS
from app.schemas.response import ApiResponse
from app.utils.response import success


router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/permissions")
def list_operation_permissions(current_user: UserProfile = Depends(require_permission("group.read"))):
    """返回角色可分配的操作权限目录。"""
    return success([{"key": item.key, "label": item.label, "domain": item.domain,
                     "operation": item.operation,
                     "operation_label": OPERATION_LABELS[item.operation],
                     "domain_label": DOMAIN_LABELS[item.domain],
                     "high_risk": item.high_risk} for item in PERMISSIONS.values()])


@router.get("/options", response_model=ApiResponse[GroupOptions])
def get_group_options(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_any_permission("group.read", "user.read")),
) -> ApiResponse[GroupOptions]:
    groups = [GroupProfile(**row) for row in group_service.list_all(db)]
    return success(GroupOptions(groups=groups))


@router.get("/page", response_model=ApiResponse[GroupPage])
def get_group_page(
    page_num: int = Query(1, ge=1, alias="pageNum"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_permission("group.read")),
) -> ApiResponse[GroupPage]:
    rows, total = group_service.list_page(db, page_num, page_size, keyword.strip() if keyword else None)
    return success(GroupPage(list=[GroupProfile(**row) for row in rows], total=total))


@router.post(
    "",
    response_model=ApiResponse[GroupProfile],
    status_code=status.HTTP_201_CREATED,
    dependencies=[operation_log("创建用户组")],
)
def create_group(
    group_in: GroupCreate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("group.create")),
) -> ApiResponse[GroupProfile]:

    if group_service.get_by_name(db, group_in.name.strip()):
        raise HTTPException(status.HTTP_409_CONFLICT, "用户组名称已存在")

    try:
        menu_ids = menu_service.normalize_role_menu_ids(db, group_in.menu_ids)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    try:
        group = group_service.create(db, group_in.model_copy(update={"menu_ids": menu_ids}))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return success(GroupProfile(**group), message="created")


@router.put(
    "/{group_id}",
    response_model=ApiResponse[GroupProfile],
    dependencies=[operation_log("修改用户组")],
)
def update_group(
    group_id: int,
    group_in: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("group.edit")),
) -> ApiResponse[GroupProfile]:

    existing_group = group_service.get_by_id(db, group_id)
    if not existing_group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户组不存在")
    if existing_group["is_admin"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "管理员组不可修改")

    name_group = group_service.get_by_name(db, group_in.name.strip())
    if name_group and name_group["id"] != group_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户组名称已存在")

    try:
        menu_ids = menu_service.normalize_role_menu_ids(db, group_in.menu_ids)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    try:
        group = group_service.update(db, group_id, group_in.model_copy(update={"menu_ids": menu_ids}))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return success(GroupProfile(**group))


@router.delete(
    "/{group_id}",
    response_model=ApiResponse[None],
    dependencies=[operation_log("删除用户组")],
)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("group.delete")),
) -> ApiResponse[GroupProfile]:

    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户组不存在")
    if group["is_system"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "系统用户组不能删除")
    if group_service.is_in_use(db, group_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户组正在使用中，不能删除")

    group_service.delete(db, group_id)
    return success(None, message="deleted")
