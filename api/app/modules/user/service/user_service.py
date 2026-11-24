import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import execute_in_session, execute_returning_one_in_session, fetch_all_in_session, fetch_one_in_session
from app.modules.user.schemas import UserCreate, UserPasswordUpdate, UserUpdate
from app.utils.datetime import to_iso_string


logger = logging.getLogger("app")


class UserService:
    """用户模块的数据访问服务，封装用户相关 SQL 操作。"""

    def _normalize_user(self, user: dict[str, Any] | None) -> dict[str, Any] | None:
        if not user:
            return None

        user.setdefault("menu_ids", [])
        user["is_admin"] = bool(user.get("is_admin"))
        user["totp_enabled"] = bool(user.get("totp_enabled"))
        user["last_login_at"] = to_iso_string(user.get("last_login_at"))
        user["login_locked_until"] = to_iso_string(user.get("login_locked_until"))
        # menu_paths 由调用方按需补全（避免循环依赖 menu 模块）
        user.setdefault("menu_paths", [])
        user.setdefault("operation_permission_keys", [])
        return user

    def _attach_menu_paths(self, db: Session, user: dict[str, Any] | None) -> dict[str, Any] | None:
        if not user:
            return None
        group_id = user.get("group_id")
        if not group_id:
            user["menu_ids"] = []
            user["menu_paths"] = []
            user["operation_permission_keys"] = []
            return user
        rows = fetch_all_in_session(
            db,
            """SELECT m.id, m.path
               FROM role_menu rm
               JOIN menu m ON m.id = rm.menu_id
               WHERE rm.role_id = :group_id
               ORDER BY m.id""",
            {"group_id": group_id},
        )
        user["menu_ids"] = [int(row["id"]) for row in rows]
        user["menu_paths"] = [row["path"] for row in rows if row.get("path")]
        operations = fetch_all_in_session(db, """SELECT permission_key FROM role_permission
            WHERE role_id = :group_id ORDER BY permission_key""", {"group_id": group_id})
        user["operation_permission_keys"] = [row["permission_key"] for row in operations]
        return user

    def _attach_menu_ids_bulk(self, db: Session, users: list[dict[str, Any]]) -> list[dict[str, Any]]:
        group_ids = sorted({int(user["group_id"]) for user in users if user.get("group_id")})
        if not group_ids:
            return users
        placeholders = ", ".join(f":g{i}" for i in range(len(group_ids)))
        rows = fetch_all_in_session(
            db,
            f"SELECT role_id, menu_id FROM role_menu WHERE role_id IN ({placeholders}) ORDER BY menu_id",
            {f"g{i}": group_id for i, group_id in enumerate(group_ids)},
        )
        mapping: dict[int, list[int]] = {}
        for row in rows:
            mapping.setdefault(int(row["role_id"]), []).append(int(row["menu_id"]))
        for user in users:
            user["menu_ids"] = mapping.get(int(user["group_id"]), []) if user.get("group_id") else []
        return users

    def get_by_id(self, db: Session, user_id: int) -> dict[str, Any] | None:
        """按用户 ID 查询用户资料。"""
        user = self._normalize_user(
            fetch_one_in_session(
                db,
                """
                SELECT u.id, u.username, u.display_name, u.email, u.is_active,
                       u.group_id, u.last_login_at, u.last_login_ip, u.login_locked_until, u.token_version,
                       g.name AS group_name, g.is_admin,
                       COALESCE(t.enabled, FALSE) AS totp_enabled
                FROM "user" u
                LEFT JOIN user_group g ON g.id = u.group_id
                LEFT JOIN user_totp t ON t.user_id = u.id
                WHERE u.id = :user_id
                """,
                {"user_id": user_id},
            )
        )
        return self._attach_menu_paths(db, user)

    def list_page(
        self,
        db: Session,
        page_num: int,
        page_size: int,
        keyword: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """分页查询用户。"""
        offset = (page_num - 1) * page_size
        params: dict[str, Any] = {"limit": page_size, "offset": offset}
        where_sql = ""
        if keyword:
            params["keyword"] = f"%{keyword}%"
            where_sql = """
            WHERE u.username ILIKE :keyword
               OR u.display_name ILIKE :keyword
               OR u.email ILIKE :keyword
            """

        rows = fetch_all_in_session(
            db,
            f"""
            SELECT u.id, u.username, u.display_name, u.email, u.is_active,
                   u.group_id, u.last_login_at, u.last_login_ip, u.login_locked_until, u.token_version,
                   g.name AS group_name, g.is_admin,
                   COALESCE(t.enabled, FALSE) AS totp_enabled
            FROM "user" u
            LEFT JOIN user_group g ON g.id = u.group_id
            LEFT JOIN user_totp t ON t.user_id = u.id
            {where_sql}
            ORDER BY u.id DESC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )
        rows = [self._normalize_user(row) for row in rows]
        rows = self._attach_menu_ids_bulk(db, rows)
        # 列表场景仅批量补全菜单 id，不展开路径和权限标识。
        total_row = fetch_one_in_session(
            db,
            f"""
            SELECT COUNT(*) AS total
            FROM "user" u
            {where_sql}
            """,
            {key: value for key, value in params.items() if key == "keyword"},
        )
        return rows, int(total_row["total"] if total_row else 0)

    def get_by_username(self, db: Session, username: str) -> dict[str, Any] | None:
        """按用户名查询用户资料（带 hashed_password，仅认证内部使用）。"""
        user = self._normalize_user(
            fetch_one_in_session(
                db,
                """
                SELECT u.id, u.username, u.display_name, u.email, u.hashed_password,
                       u.is_active, u.group_id, u.last_login_at, u.last_login_ip, u.login_locked_until, u.token_version,
                       g.name AS group_name, g.is_admin,
                       COALESCE(t.enabled, FALSE) AS totp_enabled
                FROM "user" u
                LEFT JOIN user_group g ON g.id = u.group_id
                LEFT JOIN user_totp t ON t.user_id = u.id
                WHERE u.username = :username
                """,
                {"username": username},
            )
        )
        return self._attach_menu_paths(db, user)

    def get_by_email(self, db: Session, email: str) -> dict[str, Any] | None:
        """按邮箱查询用户资料。"""
        user = self._normalize_user(
            fetch_one_in_session(
                db,
                """
                SELECT u.id, u.username, u.display_name, u.email, u.is_active,
                       u.group_id, u.last_login_at, u.last_login_ip, u.login_locked_until, u.token_version,
                       g.name AS group_name, g.is_admin,
                       COALESCE(t.enabled, FALSE) AS totp_enabled
                FROM "user" u
                LEFT JOIN user_group g ON g.id = u.group_id
                LEFT JOIN user_totp t ON t.user_id = u.id
                WHERE u.email = :email
                """,
                {"email": email},
            )
        )
        return self._attach_menu_paths(db, user)

    def create(self, db: Session, user_in: UserCreate) -> dict[str, Any]:
        """创建用户并返回新建后的用户资料。"""
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = get_password_hash(user_in.password)
        execute_in_session(
            db,
            """
            INSERT INTO "user" (username, display_name, email, hashed_password, is_active, group_id)
            VALUES (:username, :display_name, :email, :hashed_password, :is_active, :group_id)
            """,
            user_data,
        )
        return self.get_by_username(db, user_in.username)

    def update(self, db: Session, user_id: int, user_in: UserUpdate) -> dict[str, Any] | None:
        """修改用户资料并返回更新后的用户。"""
        user_data = user_in.model_dump()
        user_data["user_id"] = user_id
        execute_in_session(
            db,
            """
            UPDATE "user"
            SET display_name = :display_name,
                email = :email,
                is_active = :is_active,
                failed_login_count = CASE WHEN :is_active IS TRUE THEN 0 ELSE failed_login_count END,
                login_locked_until = CASE WHEN :is_active IS TRUE THEN NULL ELSE login_locked_until END,
                token_version = token_version + 1,
                group_id = :group_id
            WHERE id = :user_id
            """,
            user_data,
        )
        return self.get_by_id(db, user_id)

    def update_password(self, db: Session, user_id: int, password_in: UserPasswordUpdate) -> bool:
        """重置用户密码。"""
        return self.update_password_digest(db, user_id, password_in.password)

    def update_current_profile(
        self,
        db: Session,
        user_id: int,
        display_name: str,
        email: str | None,
    ) -> dict[str, Any] | None:
        """仅更新当前用户允许维护的资料字段。"""
        execute_in_session(
            db,
            """
            UPDATE "user"
            SET display_name = :display_name,
                email = :email
            WHERE id = :user_id
            """,
            {
                "user_id": user_id,
                "display_name": display_name,
                "email": email,
            },
        )
        return self.get_by_id(db, user_id)

    def update_password_digest(self, db: Session, user_id: int, password_digest: str) -> bool:
        """保存已由客户端摘要处理过的新密码，并撤销该用户的历史令牌。"""
        affected = execute_in_session(
            db,
            """
            UPDATE "user"
            SET hashed_password = :hashed_password,
                failed_login_count = 0,
                login_locked_until = NULL,
                token_version = token_version + 1
            WHERE id = :user_id
            """,
            {
                "user_id": user_id,
                "hashed_password": get_password_hash(password_digest),
            },
        )
        if affected > 0:
            logger.info("用户密码已更新，历史令牌已撤销 | 用户ID=%s", user_id)
        return affected > 0

    def record_password_login_failure(self, db: Session, user_id: int) -> bool:
        """记录密码登录失败；达到阈值后临时锁定账户。"""
        locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
        affected = execute_in_session(
            db,
            """
            UPDATE "user"
            SET failed_login_count = failed_login_count + 1,
                login_locked_until = CASE
                    WHEN failed_login_count + 1 >= :max_failures THEN :locked_until
                    ELSE NULL
                END
            WHERE id = :user_id
              AND is_active IS TRUE
            """,
            {
                "user_id": user_id,
                "max_failures": settings.LOGIN_MAX_FAILURES,
                "locked_until": locked_until,
            },
        )
        if affected > 0:
            logger.warning(
                "已记录密码登录失败 | 用户ID=%s | 最大失败次数=%s | 锁定分钟=%s",
                user_id,
                settings.LOGIN_MAX_FAILURES,
                settings.LOGIN_LOCK_MINUTES,
            )
        return affected > 0

    def reset_password_login_failures(self, db: Session, user_id: int) -> bool:
        """密码登录成功后清除连续失败次数与临时锁定状态。"""
        affected = execute_in_session(
            db,
            """
            UPDATE "user"
            SET failed_login_count = 0,
                login_locked_until = NULL
            WHERE id = :user_id
              AND (failed_login_count <> 0 OR login_locked_until IS NOT NULL)
            """,
            {"user_id": user_id},
        )
        return affected > 0

    def is_password_login_locked(self, user: dict[str, Any]) -> bool:
        locked_until = user.get("login_locked_until")
        if not locked_until:
            return False
        if isinstance(locked_until, str):
            try:
                locked_until = datetime.fromisoformat(locked_until)
            except ValueError:
                return False
        if not isinstance(locked_until, datetime):
            return False
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        return locked_until > datetime.now(timezone.utc)

    def revoke_tokens(self, db: Session, user_id: int) -> bool:
        """递增令牌版本，使该用户此前签发的 JWT 立即失效。"""
        affected = execute_in_session(
            db,
            'UPDATE "user" SET token_version = token_version + 1 WHERE id = :user_id',
            {"user_id": user_id},
        )
        if affected > 0:
            logger.info("用户令牌已撤销 | 用户ID=%s", user_id)
        return affected > 0

    def record_login(self, db: Session, user_id: int, last_login_at: datetime | None, last_login_ip: str | None) -> bool:
        """记录用户最近一次登录时间和 IP。"""
        if last_login_at is None:
            last_login_at = datetime.now(timezone.utc)
        affected = execute_in_session(
            db,
            """
            UPDATE "user"
            SET last_login_at = :last_login_at,
                last_login_ip = :last_login_ip
            WHERE id = :user_id
            """,
            {
                "user_id": user_id,
                "last_login_at": last_login_at,
                "last_login_ip": last_login_ip,
            },
        )
        return affected > 0

    def delete(self, db: Session, user_id: int) -> bool:
        """原子清理用户私有数据、转交公开资产，并安排文件清理。"""
        deleted = execute_returning_one_in_session(
            db, 'DELETE FROM "user" WHERE id = :id RETURNING id', {"id": user_id}
        )
        return deleted is not None


user_service = UserService()
