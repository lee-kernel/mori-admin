from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session


from app.core.decorators import operation_log
from app.core.security import verify_password
from app.db.session import get_db

from app.modules.auth.dependencies import get_current_user as get_current_auth_user, require_admin_permission, require_permission
from app.modules.group.service.group_service import group_service
from app.modules.user.schemas import (
    CurrentUserPasswordUpdate,
    CurrentUserProfileUpdate,
    TwoFactorDisableRequest,
    TwoFactorEnableRequest,
    TwoFactorRecoveryCodesResponse,
    TwoFactorRegenerateRequest,
    TwoFactorSetupRequest,
    TwoFactorSetupResponse,
    TwoFactorStatusResponse,
    UserCreate,
    UserPage,
    UserPasswordUpdate,
    UserProfile,
    UserUpdate,
)
from app.modules.user.service.totp_service import TwoFactorError, totp_service
from app.modules.user.service.user_service import user_service
from app.schemas.response import ApiResponse
from app.utils.response import success


router = APIRouter(prefix="/users", tags=["users"])

"""用户模块路由，最终挂载到全局 API 前缀下。"""


@router.get("/me", response_model=ApiResponse[UserProfile])
def get_current_user(
    current_user: UserProfile = Depends(get_current_auth_user),
) -> ApiResponse[UserProfile]:
    """获取当前登录用户资料。"""
    return success(current_user)


@router.put(
    "/me",
    response_model=ApiResponse[UserProfile],
    dependencies=[operation_log("修改个人资料")],
)
def update_current_user(
    user_in: CurrentUserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_auth_user),
) -> ApiResponse[UserProfile]:
    """修改当前用户的显示名称和邮箱。"""
    display_name = user_in.display_name.strip()
    if not display_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "显示名称不能为空")

    email = str(user_in.email) if user_in.email else None
    if email:
        email_user = user_service.get_by_email(db, email)
        if email_user and email_user["id"] != current_user.id:
            raise HTTPException(status.HTTP_409_CONFLICT, "邮箱已存在")

    user = user_service.update_current_profile(
        db,
        current_user.id,
        display_name,
        email,
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    return success(UserProfile(**user))


@router.put(
    "/me/password",
    response_model=ApiResponse[None],
    dependencies=[operation_log("修改个人密码")],
)
def update_current_user_password(
    password_in: CurrentUserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_auth_user),
) -> ApiResponse[None]:
    """校验当前密码后更新当前用户密码。"""
    user = user_service.get_by_username(db, current_user.username)
    if not user or not verify_password(password_in.current_password, user.get("hashed_password")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "当前密码错误")
    if password_in.current_password == password_in.new_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "新密码不能与当前密码相同")
    if not user_service.update_password_digest(db, current_user.id, password_in.new_password):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    return success(None, message="password updated")


def _verify_current_user_password(db: Session, username: str, password_digest: str) -> None:
    user = user_service.get_by_username(db, username)
    if not user or not verify_password(password_digest, user.get("hashed_password")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "当前密码错误")


@router.get("/me/2fa", response_model=ApiResponse[TwoFactorStatusResponse])
def get_current_user_2fa_status(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_auth_user),
) -> ApiResponse[TwoFactorStatusResponse]:
    """获取当前用户双因素认证状态。"""
    status_data = totp_service.get_status(db, current_user.id)
    return success(TwoFactorStatusResponse(**status_data))


@router.post("/me/2fa/setup", response_model=ApiResponse[TwoFactorSetupResponse])
def setup_current_user_2fa(
    payload_in: TwoFactorSetupRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_auth_user),
) -> ApiResponse[TwoFactorSetupResponse]:
    """校验当前密码并生成 2FA 绑定二维码信息。"""
    _verify_current_user_password(db, current_user.username, payload_in.current_password)
    try:
        setup_data = totp_service.start_setup(db, current_user.id, current_user.username)
    except TwoFactorError as exc:
        raise HTTPException(exc.status_code, exc.message) from None
    return success(TwoFactorSetupResponse(**setup_data))


@router.post(
    "/me/2fa/enable",
    response_model=ApiResponse[TwoFactorRecoveryCodesResponse],
    dependencies=[operation_log("开启双因素认证")],
)
def enable_current_user_2fa(
    payload_in: TwoFactorEnableRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_auth_user),
) -> ApiResponse[TwoFactorRecoveryCodesResponse]:
    """校验动态码正式开启 2FA，并一次性返回恢复码。"""
    try:
        codes = totp_service.enable(db, current_user.id, payload_in.code)
    except TwoFactorError as exc:
        raise HTTPException(exc.status_code, exc.message) from None
    return success(TwoFactorRecoveryCodesResponse(recovery_codes=codes), message="2fa enabled")


@router.post(
    "/me/2fa/disable",
    response_model=ApiResponse[None],
    dependencies=[operation_log("关闭双因素认证")],
)
def disable_current_user_2fa(
    payload_in: TwoFactorDisableRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_auth_user),
) -> ApiResponse[None]:
    """校验当前密码及动态码/恢复码后关闭 2FA。"""
    _verify_current_user_password(db, current_user.username, payload_in.current_password)
    try:
        totp_service.disable(db, current_user.id, payload_in.code, payload_in.method)
    except TwoFactorError as exc:
        raise HTTPException(exc.status_code, exc.message) from None
    return success(None, message="2fa disabled")


@router.post(
    "/me/2fa/recovery-codes/regenerate",
    response_model=ApiResponse[TwoFactorRecoveryCodesResponse],
    dependencies=[operation_log("重置2FA恢复码")],
)
def regenerate_current_user_2fa_recovery_codes(
    payload_in: TwoFactorRegenerateRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_auth_user),
) -> ApiResponse[TwoFactorRecoveryCodesResponse]:
    """校验当前密码及动态码后重新生成一次性恢复码。"""
    _verify_current_user_password(db, current_user.username, payload_in.current_password)
    try:
        codes = totp_service.regenerate_recovery_codes(db, current_user.id, payload_in.code)
    except TwoFactorError as exc:
        raise HTTPException(exc.status_code, exc.message) from None
    return success(TwoFactorRecoveryCodesResponse(recovery_codes=codes), message="recovery codes regenerated")


@router.get("/page", response_model=ApiResponse[UserPage])
def get_user_page(
    page_num: int = Query(1, ge=1, alias="pageNum"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_permission("user.read")),
) -> ApiResponse[UserPage]:
    """分页查询用户列表。"""
    rows, total = user_service.list_page(db, page_num, page_size, keyword.strip() if keyword else None)
    return success(UserPage(list=[UserProfile(**row) for row in rows], total=total))


@router.get("/{user_id}", response_model=ApiResponse[UserProfile])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_permission("user.read")),
) -> ApiResponse[UserProfile]:
    """按用户 ID 获取用户资料。"""
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return success(UserProfile(**user))


@router.post(
    "",
    response_model=ApiResponse[UserProfile],
    status_code=status.HTTP_201_CREATED,
    dependencies=[operation_log("创建用户")],
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("user.create")),
) -> ApiResponse[UserProfile]:

    """创建用户；用户名重复时返回冲突错误。"""
    existing_user = user_service.get_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已存在")
    if user_in.group_id and not group_service.get_by_id(db, user_in.group_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户组不存在")

    user = user_service.create(db, user_in)
    return success(UserProfile(**user), message="created")


@router.put(
    "/{user_id}",
    response_model=ApiResponse[UserProfile],
    dependencies=[operation_log("修改用户")],
)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("user.edit")),
) -> ApiResponse[UserProfile]:

    """修改用户资料。"""
    existing = user_service.get_by_id(db, user_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if existing["username"] == "admin" and (
        not user_in.is_active or user_in.group_id != existing["group_id"]
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "默认管理员的状态与用户组不可修改")

    if user_in.email:
        email_user = user_service.get_by_email(db, user_in.email)
        if email_user and email_user["id"] != user_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "邮箱已存在")
    if user_in.group_id and not group_service.get_by_id(db, user_in.group_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户组不存在")

    user = user_service.update(db, user_id, user_in)
    return success(UserProfile(**user))


@router.put(
    "/{user_id}/password",
    response_model=ApiResponse[None],
    dependencies=[operation_log("重置用户密码")],
)
def update_user_password(
    user_id: int,
    password_in: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("user.edit")),
) -> ApiResponse[None]:

    """重置用户密码。"""
    target = user_service.get_by_id(db, user_id)
    if target and target["username"] == "admin":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "默认管理员请在账户中心修改密码")
    if not user_service.update_password(db, user_id, password_in):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    return success(None, message="password updated")


@router.delete(
    "/{user_id}/2fa",
    response_model=ApiResponse[None],
    dependencies=[operation_log("重置用户双因素认证")],
)
def reset_user_2fa(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("user.edit")),
) -> ApiResponse[None]:
    """管理员重置指定用户的双因素认证。"""
    target = user_service.get_by_id(db, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if target["username"] == "admin":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "默认管理员请在账户中心管理双因素认证")
    if not target.get("totp_enabled"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "该用户未开启双因素认证")
    totp_service.admin_reset(db, user_id)
    return success(None, message="2fa reset")


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[None],
    dependencies=[operation_log("删除用户")],
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("user.delete")),
) -> ApiResponse[None]:

    """删除账号，保留审计记录。"""
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if user["username"] == "admin":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "默认管理员不能删除")

    if not user_service.delete(db, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    return success(None, message="deleted")
