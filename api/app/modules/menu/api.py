from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin_permission, require_any_permission, require_permission
from app.modules.menu.schemas import MenuCreate, MenuItem, MenuList, MenuTree, MenuUpdate
from app.modules.menu.service.menu_service import menu_service
from app.modules.user.schemas import UserProfile
from app.schemas.response import ApiResponse
from app.utils.response import success


# /mine 仅要求已登录，返回当前用户可见的菜单树（用于前端动态路由）。
router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("/tree", response_model=ApiResponse[MenuTree])
def list_menu_tree(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_any_permission("menu.read", "group.read")),
) -> ApiResponse[MenuTree]:
    """返回完整的菜单树，供「菜单管理」页面使用。"""
    return success(MenuTree(list=menu_service.list_tree(db)))


@router.get("/all", response_model=ApiResponse[MenuList])
def list_menu_all(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_any_permission("menu.read", "group.read")),
) -> ApiResponse[MenuList]:
    """返回扁平的全量菜单列表，主要给「用户组配置」页选择菜单时使用。"""
    rows = menu_service.list_all(db)
    return success(MenuList(list=[MenuItem(**row) for row in rows]))


@router.get("/mine", response_model=ApiResponse[MenuTree])
def list_my_menus(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MenuTree]:
    """返回当前登录用户可见的菜单树，前端据此构建动态路由。"""
    tree = menu_service.list_tree(db) if current_user.is_admin else menu_service.list_tree_for_ids(db, current_user.menu_ids)
    return success(MenuTree(list=tree))


@router.post("", response_model=ApiResponse[MenuItem], status_code=status.HTTP_201_CREATED)
def create_menu(
    menu_in: MenuCreate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("menu.create")),
) -> ApiResponse[MenuItem]:
    """新建菜单。校验：路径唯一、上级存在。"""
    path = menu_in.path.strip()
    if menu_service.get_by_path(db, path):
        raise HTTPException(status.HTTP_409_CONFLICT, "菜单路径已存在")
    if menu_service.get_by_permission_key(db, menu_in.permission_key.strip()):
        raise HTTPException(status.HTTP_409_CONFLICT, "权限标识已存在")
    if menu_in.parent_id and not menu_service.get_by_id(db, menu_in.parent_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "上级菜单不存在")

    menu = menu_service.create(db, menu_in)
    return success(MenuItem(**menu), message="created")


@router.put("/{menu_id}", response_model=ApiResponse[MenuItem])
def update_menu(
    menu_id: int,
    menu_in: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("menu.edit")),
) -> ApiResponse[MenuItem]:
    """更新菜单。校验：菜单存在、上级合法、路径唯一。"""
    existing = menu_service.get_by_id(db, menu_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "菜单不存在")
    if existing["is_system"] and menu_in.permission_key.strip() != existing["permission_key"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "系统内置菜单的权限标识不能修改")

    # 不允许将自己设为自己的上级
    if menu_in.parent_id == menu_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "上级菜单不能选择自身")
    if menu_in.parent_id and not menu_service.get_by_id(db, menu_in.parent_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "上级菜单不存在")
    if menu_service.would_create_cycle(db, menu_id, menu_in.parent_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能将菜单移动到自身的下级")

    # 路径必须保持唯一（允许命中自身）
    path = menu_in.path.strip()
    path_owner = menu_service.get_by_path(db, path)
    if path_owner and path_owner["id"] != menu_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "菜单路径已存在")
    permission_owner = menu_service.get_by_permission_key(db, menu_in.permission_key.strip())
    if permission_owner and permission_owner["id"] != menu_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "权限标识已存在")

    access_fields = ("parent_id", "path", "permission_key", "component", "redirect", "hidden", "is_external")
    access_changed = any(existing.get(field) != getattr(menu_in, field) for field in access_fields)
    menu = menu_service.update(db, menu_id, menu_in)
    if access_changed:
        menu_service.revoke_users_for_menu(db, menu_id)
    return success(MenuItem(**menu))


@router.delete("/{menu_id}", response_model=ApiResponse[None])
def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_admin_permission("menu.delete")),
) -> ApiResponse[None]:
    """删除菜单。系统内置菜单不可删；存在子菜单时需先删子菜单。"""
    menu = menu_service.get_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "菜单不存在")
    if menu["is_system"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "系统内置菜单不能删除")
    if menu_service.has_children(db, menu_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请先删除子菜单")

    menu_service.revoke_users_for_menu(db, menu_id)
    menu_service.delete(db, menu_id)
    return success(None, message="deleted")
