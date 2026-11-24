from getpass import getpass

from app.core.security import digest_password_for_transport, get_password_hash
from app.db.init_db import init_db
from app.db.session import SessionLocal, execute_in_session


def main() -> None:
    password = getpass("设置管理员 admin 的密码（至少 12 个字符）：")
    if len(password) < 12 or len(password) > 256:
        raise SystemExit("管理员密码长度须为 12 至 256 个字符")
    if getpass("再次输入密码：") != password:
        raise SystemExit("两次输入的密码不同")

    with SessionLocal() as db:
        init_db(db)
        result = execute_in_session(
            db,
            """INSERT INTO "user" (username, display_name, hashed_password, group_id)
               VALUES ('admin', 'Administrator', :password,
                       (SELECT id FROM user_group WHERE is_admin))
               ON CONFLICT (username) DO NOTHING""",
            {"password": get_password_hash(digest_password_for_transport(password))},
        )
    if result != 1:
        raise SystemExit("管理员 admin 已存在")
    print("管理员 admin 已创建")


if __name__ == "__main__":
    main()
