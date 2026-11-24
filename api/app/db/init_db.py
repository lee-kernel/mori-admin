from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import execute_in_session, fetch_all_in_session, fetch_one_in_session
from app.db.sql import split_statements
from app.modules.access_control.catalog import PERMISSIONS
from app.modules.menu.service.menu_service import FOUNDATION_MENU_KEYS

INIT_SQL_PATH = Path(__file__).parent / "init.sql"
MIGRATIONS: tuple[tuple[int, Path], ...] = (
    (1, INIT_SQL_PATH.parent / "migrations" / "002_branding.sql"),
    (2, INIT_SQL_PATH.parent / "migrations" / "003_totp_2fa.sql"),
)
SCHEMA_VERSION = 3


def _run_sql_file(db: Session, path: Path) -> None:
    script = path.read_text(encoding="utf-8")
    for statement in split_statements(script):
        execute_in_session(db, statement, commit=False)


def init_db(db: Session) -> None:
    """初始化空库或按版本升级已有数据库。"""
    try:
        # 同一数据库的多个启动进程串行创建基线与种子。
        execute_in_session(db, "SELECT pg_advisory_xact_lock(1842340621)", commit=False)
        _init_or_upgrade(db)
        db.commit()
    except Exception:
        db.rollback()
        raise


def _init_or_upgrade(db: Session) -> None:
    initialized = fetch_one_in_session(
        db,
        "SELECT to_regclass('public.mori_admin_schema_version') IS NOT NULL AS initialized",
    )
    if initialized and initialized["initialized"]:
        version = fetch_one_in_session(db, "SELECT version FROM mori_admin_schema_version")
        current_version = int(version["version"]) if version else None
        if current_version is None or current_version > SCHEMA_VERSION:
            raise RuntimeError("数据库版本不受当前程序支持")
        for expected_version, migration_path in MIGRATIONS:
            if current_version == expected_version:
                _run_sql_file(db, migration_path)
                current_version += 1
        if current_version != SCHEMA_VERSION:
            raise RuntimeError("数据库版本不受当前程序支持")
        return
    existing = fetch_one_in_session(
        db, "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public') AS occupied"
    )
    if existing and existing["occupied"]:
        raise RuntimeError("请为 Mori Admin 使用独立的空数据库")
    _run_sql_file(db, INIT_SQL_PATH)
    seed_db(db)


def seed_operation_permissions(db: Session) -> None:
    """从唯一权限目录写入静态权限，供新库初始化与隔离测试复用。"""
    for permission in PERMISSIONS.values():
        execute_in_session(db, """INSERT INTO operation_permission
            (key, label, domain, operation, high_risk)
            VALUES (:key, :label, :domain, :operation, :high_risk)
            ON CONFLICT (key) DO NOTHING""", vars(permission), commit=False)


def seed_db(db: Session) -> None:
    seed_operation_permissions(db)
    menus = fetch_all_in_session(db, 'SELECT id, permission_key FROM "menu"')
    seed_group(db, "管理员组", "拥有系统管理权限", [row["id"] for row in menus],
               list(PERMISSIONS), True, True)
    seed_group(db, "普通用户组", "可使用首页和账户中心",
               [row["id"] for row in menus if row["permission_key"] in FOUNDATION_MENU_KEYS], [], True, False)


def seed_group(db: Session, name: str, description: str, menu_ids: list[int],
               permission_keys: list[str], is_system: bool, is_admin: bool) -> None:
    normalized_ids = sorted(set(menu_ids))
    granted = sorted(set(permission_keys))
    if set(granted) - PERMISSIONS.keys():
        raise ValueError("默认用户组操作权限不存在")
    execute_in_session(
        db,
        """INSERT INTO "user_group" (name, description, is_system, is_admin)
           VALUES (:name, :description, :is_system, :is_admin)
           ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description,
               is_system = EXCLUDED.is_system, is_admin = EXCLUDED.is_admin""",
        {"name": name, "description": description, "is_system": is_system, "is_admin": is_admin},
        commit=False,
    )
    group = fetch_one_in_session(db, 'SELECT id FROM "user_group" WHERE name = :name', {"name": name})
    execute_in_session(
        db,
        'DELETE FROM "role_menu" WHERE role_id = :role_id',
        {"role_id": group["id"]},
        commit=False,
    )
    for menu_id in normalized_ids:
        execute_in_session(
            db,
            'INSERT INTO "role_menu" (role_id, menu_id) VALUES (:role_id, :menu_id)',
            {"role_id": group["id"], "menu_id": menu_id},
            commit=False,
        )
    execute_in_session(db, 'DELETE FROM role_permission WHERE role_id = :role_id',
                       {"role_id": group["id"]}, commit=False)
    for key in granted:
        execute_in_session(db, """INSERT INTO role_permission (role_id, permission_key)
            VALUES (:role_id, :permission_key)""",
            {"role_id": group["id"], "permission_key": key}, commit=False)
