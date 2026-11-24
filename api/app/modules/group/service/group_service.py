from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import execute_in_session, fetch_all_in_session, fetch_one_in_session, insert_in_session
from app.modules.group.schemas import GroupCreate, GroupUpdate
from app.modules.access_control.catalog import PERMISSIONS


class GroupService:
    """用户组持久化；role_menu 仅决定导航，role_permission 决定操作授权。"""

    def _normalize_group(self, group: dict[str, Any] | None) -> dict[str, Any] | None:
        if not group:
            return None

        group["menu_ids"] = sorted({int(mid) for mid in group.get("menu_ids", [])})
        group["is_system"] = bool(group.get("is_system"))
        group["is_admin"] = bool(group.get("is_admin"))
        return group

    def _attach_menu_ids(self, db: Session, group: dict[str, Any] | None) -> dict[str, Any] | None:
        if not group:
            return None
        rows = fetch_all_in_session(
            db,
            "SELECT menu_id FROM role_menu WHERE role_id = :role_id ORDER BY menu_id",
            {"role_id": group["id"]},
        )
        group["menu_ids"] = [int(row["menu_id"]) for row in rows]
        permissions = fetch_all_in_session(db, """SELECT permission_key FROM role_permission
            WHERE role_id = :role_id ORDER BY permission_key""", {"role_id": group["id"]})
        group["permission_keys"] = [row["permission_key"] for row in permissions]
        return self._normalize_group(group)

    def _attach_menu_ids_bulk(self, db: Session, groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not groups:
            return []
        placeholders = ", ".join(f":g{i}" for i in range(len(groups)))
        params = {f"g{i}": group["id"] for i, group in enumerate(groups)}
        rows = fetch_all_in_session(
            db,
            f"SELECT role_id, menu_id FROM role_menu WHERE role_id IN ({placeholders}) ORDER BY menu_id",
            params,
        )
        mapping: dict[int, list[int]] = {}
        for row in rows:
            mapping.setdefault(int(row["role_id"]), []).append(int(row["menu_id"]))
        for group in groups:
            group["menu_ids"] = mapping.get(int(group["id"]), [])
        permissions = fetch_all_in_session(db, """SELECT role_id, permission_key FROM role_permission
            WHERE role_id IN (""" + placeholders + ") ORDER BY permission_key", params)
        permission_map: dict[int, list[str]] = {}
        for row in permissions:
            permission_map.setdefault(int(row["role_id"]), []).append(row["permission_key"])
        for group in groups:
            group["permission_keys"] = permission_map.get(int(group["id"]), [])
        return [self._normalize_group(group) for group in groups]

    def _replace_menu_ids(self, db: Session, group_id: int, menu_ids: list[int]) -> None:
        normalized = sorted({int(mid) for mid in menu_ids})
        db.execute(text("DELETE FROM role_menu WHERE role_id = :role_id"), {"role_id": group_id})
        if normalized:
            db.execute(
                text("INSERT INTO role_menu (role_id, menu_id) VALUES (:role_id, :menu_id)"),
                [{"role_id": group_id, "menu_id": mid} for mid in normalized],
            )
    def _replace_permissions(self, db: Session, group_id: int, keys: list[str]) -> None:
        normalized = sorted(set(keys))
        if set(normalized) - PERMISSIONS.keys():
            raise ValueError("操作权限不存在")
        execute_in_session(db, "DELETE FROM role_permission WHERE role_id = :role_id",
                           {"role_id": group_id}, commit=False)
        for key in normalized:
            execute_in_session(db, """INSERT INTO role_permission (role_id, permission_key)
                VALUES (:role_id, :permission_key)""",
                {"role_id": group_id, "permission_key": key}, commit=False)

    def get_by_id(self, db: Session, group_id: int) -> dict[str, Any] | None:
        return self._attach_menu_ids(
            db,
            self._normalize_group(
                fetch_one_in_session(
                    db,
                    """
                    SELECT id, name, description, is_system, is_admin
                    FROM user_group
                    WHERE id = :group_id
                    """,
                    {"group_id": group_id},
                )
            )
        )

    def get_by_name(self, db: Session, name: str) -> dict[str, Any] | None:
        return self._attach_menu_ids(
            db,
            self._normalize_group(
                fetch_one_in_session(
                    db,
                    """
                    SELECT id, name, description, is_system, is_admin
                    FROM user_group
                    WHERE name = :name
                    """,
                    {"name": name},
                )
            )
        )

    def list_page(
        self,
        db: Session,
        page_num: int,
        page_size: int,
        keyword: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        offset = (page_num - 1) * page_size
        params: dict[str, Any] = {"limit": page_size, "offset": offset}
        where_sql = ""
        if keyword:
            params["keyword"] = f"%{keyword}%"
            where_sql = """
            WHERE name ILIKE :keyword
               OR description ILIKE :keyword
            """

        rows = fetch_all_in_session(
            db,
            f"""
            SELECT id, name, description, is_system, is_admin
            FROM user_group
            {where_sql}
            ORDER BY is_system DESC, id ASC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )
        total_row = fetch_one_in_session(
            db,
            f"""
            SELECT COUNT(*) AS total
            FROM user_group
            {where_sql}
            """,
            {key: value for key, value in params.items() if key == "keyword"},
        )
        return self._attach_menu_ids_bulk(db, rows), int(total_row["total"] if total_row else 0)

    def list_all(self, db: Session) -> list[dict[str, Any]]:
        rows = fetch_all_in_session(
            db,
            """
            SELECT id, name, description, is_system, is_admin
            FROM user_group
            ORDER BY is_system DESC, id ASC
            """,
        )
        return self._attach_menu_ids_bulk(db, rows)

    def create(self, db: Session, group_in: GroupCreate) -> dict[str, Any]:
        try:
            group_id = insert_in_session(
                db,
                """INSERT INTO user_group (name, description, is_system, is_admin)
                   VALUES (:name, :description, FALSE, FALSE)
                   RETURNING id""",
                {"name": group_in.name.strip(), "description": group_in.description},
                commit=False,
            )
            self._replace_menu_ids(db, group_id, group_in.menu_ids)
            self._replace_permissions(db, group_id, group_in.permission_keys)
            db.commit()
        except Exception:
            db.rollback()
            raise
        return self.get_by_id(db, group_id)

    def update(self, db: Session, group_id: int, group_in: GroupUpdate) -> dict[str, Any] | None:
        existing = self.get_by_id(db, group_id)
        if not existing:
            return None
        if existing["is_admin"]:
            raise ValueError("管理员组不可修改")
        try:
            db.execute(
                text("UPDATE user_group SET name = :name, description = :description WHERE id = :group_id"),
                {"group_id": group_id, "name": group_in.name.strip(), "description": group_in.description},
            )
            self._replace_menu_ids(db, group_id, group_in.menu_ids)
            self._replace_permissions(db, group_id, group_in.permission_keys)
            if set(existing["menu_ids"]) != set(group_in.menu_ids) or set(existing["permission_keys"]) != set(group_in.permission_keys):
                db.execute(
                    text('UPDATE "user" SET token_version = token_version + 1 WHERE group_id = :group_id'),
                    {"group_id": group_id},
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        return self.get_by_id(db, group_id)

    def is_in_use(self, db: Session, group_id: int) -> bool:
        row = fetch_one_in_session(
            db,
            'SELECT COUNT(*) AS total FROM "user" WHERE group_id = :group_id',
            {"group_id": group_id},
        )
        return bool(row and int(row["total"]) > 0)

    def delete(self, db: Session, group_id: int) -> bool:
        affected = execute_in_session(
            db,
            "DELETE FROM user_group WHERE id = :group_id",
            {"group_id": group_id},
        )
        return affected > 0


group_service = GroupService()
