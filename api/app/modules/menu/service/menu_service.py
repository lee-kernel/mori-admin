from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.session import execute_in_session, fetch_all_in_session, fetch_one_in_session
from app.modules.menu.schemas import MenuCreate, MenuNode, MenuUpdate


FOUNDATION_MENU_KEYS = {"home", "dashboard", "account", "account:profile", "account:security"}


class MenuService:
    """菜单数据访问服务，封装 menu 表 CRUD 与树形构建逻辑。"""

    def _normalize(self, row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        row["hidden"] = bool(row.get("hidden"))
        row["is_external"] = bool(row.get("is_external"))
        row["is_system"] = bool(row.get("is_system"))
        if row.get("parent_id") in (0, None):
            row["parent_id"] = None
        return row

    def list_all(self, db: Session) -> list[dict[str, Any]]:
        rows = fetch_all_in_session(
            db,
            """
            SELECT id, parent_id, name, path, permission_key, component, icon, redirect,
                   sort, hidden, is_external, is_system
            FROM menu
            ORDER BY COALESCE(parent_id, 0) ASC, sort ASC, id ASC
            """,
        )
        return [self._normalize(row) for row in rows]

    def get_by_id(self, db: Session, menu_id: int) -> dict[str, Any] | None:
        return self._normalize(
            fetch_one_in_session(
                db,
                """
                SELECT id, parent_id, name, path, permission_key, component, icon, redirect,
                       sort, hidden, is_external, is_system
                FROM menu
                WHERE id = :menu_id
                """,
                {"menu_id": menu_id},
            )
        )

    def get_by_path(self, db: Session, path: str) -> dict[str, Any] | None:
        return self._normalize(
            fetch_one_in_session(
                db,
                """
                SELECT id, parent_id, name, path, permission_key, component, icon, redirect,
                       sort, hidden, is_external, is_system
                FROM menu
                WHERE path = :path
                """,
                {"path": path},
            )
        )

    def get_by_permission_key(self, db: Session, permission_key: str) -> dict[str, Any] | None:
        return self._normalize(
            fetch_one_in_session(
                db,
                """
                SELECT id, parent_id, name, path, permission_key, component, icon, redirect,
                       sort, hidden, is_external, is_system
                FROM menu
                WHERE permission_key = :permission_key
                """,
                {"permission_key": permission_key},
            )
        )

    def create(self, db: Session, menu_in: MenuCreate, is_system: bool = False) -> dict[str, Any]:
        execute_in_session(
            db,
            """
            INSERT INTO menu
                (parent_id, name, path, permission_key, component, icon, redirect, sort, hidden, is_external, is_system)
            VALUES
                (:parent_id, :name, :path, :permission_key, :component, :icon, :redirect, :sort, :hidden, :is_external, :is_system)
            """,
            {
                "parent_id": menu_in.parent_id,
                "name": menu_in.name.strip(),
                "path": menu_in.path.strip(),
                "permission_key": menu_in.permission_key.strip(),
                "component": menu_in.component,
                "icon": menu_in.icon,
                "redirect": menu_in.redirect,
                "sort": menu_in.sort,
                "hidden": menu_in.hidden,
                "is_external": menu_in.is_external,
                "is_system": is_system,
            },
        )
        return self.get_by_path(db, menu_in.path.strip())

    def update(self, db: Session, menu_id: int, menu_in: MenuUpdate) -> dict[str, Any] | None:
        execute_in_session(
            db,
            """
            UPDATE menu
            SET parent_id = :parent_id,
                name = :name,
                path = :path,
                permission_key = :permission_key,
                component = :component,
                icon = :icon,
                redirect = :redirect,
                sort = :sort,
                hidden = :hidden,
                is_external = :is_external
            WHERE id = :menu_id
            """,
            {
                "menu_id": menu_id,
                "parent_id": menu_in.parent_id,
                "name": menu_in.name.strip(),
                "path": menu_in.path.strip(),
                "permission_key": menu_in.permission_key.strip(),
                "component": menu_in.component,
                "icon": menu_in.icon,
                "redirect": menu_in.redirect,
                "sort": menu_in.sort,
                "hidden": menu_in.hidden,
                "is_external": menu_in.is_external,
            },
        )
        return self.get_by_id(db, menu_id)

    def delete(self, db: Session, menu_id: int) -> bool:
        affected = execute_in_session(
            db,
            "DELETE FROM menu WHERE id = :menu_id",
            {"menu_id": menu_id},
        )
        return affected > 0

    def has_children(self, db: Session, menu_id: int) -> bool:
        row = fetch_one_in_session(
            db,
            "SELECT COUNT(*) AS total FROM menu WHERE parent_id = :parent_id",
            {"parent_id": menu_id},
        )
        return bool(row and int(row["total"]) > 0)

    def would_create_cycle(self, db: Session, menu_id: int, parent_id: int | None) -> bool:
        """判断把菜单移动到目标父节点后是否会形成环。"""
        current = parent_id
        visited: set[int] = set()
        while current:
            if current == menu_id or current in visited:
                return True
            visited.add(current)
            parent = self.get_by_id(db, current)
            current = parent.get("parent_id") if parent else None
        return False

    def normalize_role_menu_ids(self, db: Session, menu_ids: list[int]) -> list[int]:
        """校验授权菜单并自动补齐祖先目录。"""
        requested = {int(mid) for mid in menu_ids}
        if not requested:
            return []
        rows = self.list_all(db)
        by_id = {int(row["id"]): row for row in rows}
        missing = requested - by_id.keys()
        if missing:
            raise ValueError(f"菜单不存在：{', '.join(map(str, sorted(missing)))}")
        normalized = set(requested)
        for menu_id in requested:
            parent_id = by_id[menu_id].get("parent_id")
            while parent_id:
                normalized.add(int(parent_id))
                parent_id = by_id[int(parent_id)].get("parent_id")
        return sorted(normalized)

    def revoke_users_for_menu(self, db: Session, menu_id: int) -> None:
        """菜单配置变化后撤销受影响角色成员的旧令牌。"""
        execute_in_session(
            db,
            """UPDATE "user"
               SET token_version = token_version + 1
               WHERE group_id IN (SELECT role_id FROM role_menu WHERE menu_id = :menu_id)""",
            {"menu_id": menu_id},
        )

    def build_tree(self, rows: list[dict[str, Any]]) -> list[MenuNode]:
        """将扁平列表构建为树。"""
        nodes: dict[int, MenuNode] = {row["id"]: MenuNode(**row) for row in rows}
        roots: list[MenuNode] = []
        for row in rows:
            node = nodes[row["id"]]
            parent_id = row.get("parent_id")
            if parent_id and parent_id in nodes:
                nodes[parent_id].children.append(node)
            else:
                roots.append(node)
        return roots

    def list_tree(self, db: Session) -> list[MenuNode]:
        return self.build_tree(self.list_all(db))

    def list_tree_for_ids(self, db: Session, menu_ids: list[int]) -> list[MenuNode]:
        """构建包含给定 id 的菜单子树；自动补全父节点以保证连通性。"""
        all_rows = self.list_all(db)
        by_id = {row["id"]: row for row in all_rows}

        keep = {row["id"] for row in all_rows if row["permission_key"] in FOUNDATION_MENU_KEYS}
        for mid in menu_ids:
            cur = mid
            while cur and cur in by_id and cur not in keep:
                keep.add(cur)
                cur = by_id[cur].get("parent_id")

        filtered = [row for row in all_rows if row["id"] in keep]
        return self.build_tree(filtered)

    def collect_paths(self, nodes: list[MenuNode]) -> list[str]:
        result: list[str] = []

        def walk(node: MenuNode) -> None:
            if node.path:
                result.append(node.path)
            for child in node.children:
                walk(child)

        for node in nodes:
            walk(node)
        return result


menu_service = MenuService()
