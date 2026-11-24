from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.user.schemas import UserProfile
from app.modules.user.service.user_service import user_service
from app.modules.access_control.catalog import get_permission


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserProfile:
    payload = decode_access_token(token)
    username = payload.get("sub") if payload else None
    user_id = payload.get("uid") if payload else None
    purpose = payload.get("purpose", "access") if payload else None
    if purpose != "access" or not username or not isinstance(user_id, int) or user_id <= 0:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已过期，请重新登录")

    user = user_service.get_by_username(db, username)
    if not user or int(user["id"]) != user_id or not user.get("is_active"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在或已被禁用")
    if int(payload.get("ver", -1)) != int(user.get("token_version", 0)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已失效，请重新登录")
    return UserProfile(**user)


def require_permission(permission_key: str):
    """只以用户组的操作权限授权，未知权限键默认拒绝。"""

    def checker(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if get_permission(permission_key) is None or permission_key not in current_user.operation_permission_keys:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "权限不足")
        return current_user

    return checker


def require_any_permission(*permission_keys: str):
    """要求当前用户至少拥有一个指定权限。"""

    def checker(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if not any(get_permission(key) is not None and key in current_user.operation_permission_keys
                   for key in permission_keys):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "权限不足")
        return current_user

    return checker


def require_admin_permission(permission_key: str):
    """身份、授权与导航写入需同时验证管理员身份和操作权限。"""

    def checker(current_user: UserProfile = Depends(require_permission(permission_key))) -> UserProfile:
        if not current_user.is_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
        return current_user

    return checker
