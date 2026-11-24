from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.tracing import current_trace_id
from app.db.session import fetch_all_in_session, fetch_one_in_session, insert_in_session
from app.utils.datetime import to_iso_string, to_utc_datetime


class LogService:
    """日志模块的数据访问服务。"""

    # ── 登录日志 ──────────────────────────────────────────────

    def create_login_log(
        self,
        db: Session,
        user_id: int | None,
        username: str | None,
        ip_address: str | None,
        platform: str | None,
        browser: str | None,
        event_type: int = 1,
        login_at: datetime | None = None,
    ) -> int:
        """写入一条登录日志，返回新记录 ID。"""
        ts = to_utc_datetime(login_at) if login_at else datetime.now(timezone.utc)
        return insert_in_session(
            db,
            """
                INSERT INTO login_log (trace_id, user_id, username, ip_address, platform, browser, event_type, login_at)
                VALUES (:trace_id, :user_id, :username, :ip_address, :platform, :browser, :event_type, :login_at)
                RETURNING id
            """,
            {
                "trace_id": current_trace_id(),
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "platform": platform,
                "browser": browser,
                "event_type": event_type,
                "login_at": ts,
            },
        )

    def list_login_log_page(
        self,
        db: Session,
        page_num: int,
        page_size: int,
        username: str | None = None,
        ip_address: str | None = None,
        platform: str | None = None,
        event_type: int | None = None,
        trace_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """分页查询登录日志。"""
        offset = (page_num - 1) * page_size
        conditions: list[str] = []
        params: dict[str, Any] = {"limit": page_size, "offset": offset}

        if username:
            conditions.append("username ILIKE :username")
            params["username"] = f"%{username}%"
        if ip_address:
            conditions.append("ip_address ILIKE :ip_address")
            params["ip_address"] = f"%{ip_address}%"
        if platform:
            conditions.append("platform ILIKE :platform")
            params["platform"] = f"%{platform}%"
        if event_type is not None:
            conditions.append("event_type = :event_type")
            params["event_type"] = event_type
        if trace_id:
            conditions.append("trace_id = :trace_id")
            params["trace_id"] = trace_id
        if start_time:
            conditions.append("login_at >= :start_time")
            params["start_time"] = to_utc_datetime(start_time)
        if end_time:
            conditions.append("login_at <= :end_time")
            params["end_time"] = to_utc_datetime(end_time)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        total_row = fetch_one_in_session(
            db,
            f"SELECT COUNT(*) AS total FROM login_log {where_sql}",
            params,
        )
        total = int(total_row["total"]) if total_row else 0

        rows = fetch_all_in_session(
            db,
            f"""
            SELECT id, trace_id, user_id, username, ip_address, platform, browser, event_type, login_at
            FROM login_log
            {where_sql}
            ORDER BY login_at DESC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )


        for row in rows:
            row["login_at"] = to_iso_string(row.get("login_at"))

        return rows, total

    # ── 操作记录 ──────────────────────────────────────────────

    def create_operation_log(
        self,
        db: Session,
        user_id: int | None,
        username: str | None,
        method: str,
        url: str,
        status_code: int,
        duration_ms: int,
        title: str | None = None,
        operated_at: datetime | None = None,
    ) -> int:
        """写入一条操作记录，返回新记录 ID。"""
        ts = to_utc_datetime(operated_at) if operated_at else datetime.now(timezone.utc)
        return insert_in_session(
            db,
            """
                INSERT INTO operation_log (trace_id, user_id, username, method, url, title, status_code, duration_ms, operated_at)
                VALUES (:trace_id, :user_id, :username, :method, :url, :title, :status_code, :duration_ms, :operated_at)
                RETURNING id
            """,
            {
                "trace_id": current_trace_id(),
                "user_id": user_id,
                "username": username,
                "method": method,
                "url": url,
                "title": title,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "operated_at": ts,
            },
        )

    def list_recent_operation_logs(
        self,
        db: Session,
        start_time: datetime,
        limit: int,
        username: str | None = None,
    ) -> list[dict[str, Any]]:
        """查询最近一段时间内的操作记录（不分页），供异常检测等只读分析场景使用。"""
        conditions = ["operated_at >= :start_time"]
        params: dict[str, Any] = {
            "start_time": to_utc_datetime(start_time),
            "limit": limit,
        }

        if username:
            conditions.append("username = :username")
            params["username"] = username

        where_sql = f"WHERE {' AND '.join(conditions)}"

        rows = fetch_all_in_session(
            db,
            f"""
            SELECT id, trace_id, user_id, username, method, url, title, status_code, duration_ms, operated_at
            FROM operation_log
            {where_sql}
            ORDER BY operated_at DESC
            LIMIT :limit
            """,
            params,
        )

        for row in rows:
            row["operated_at"] = to_iso_string(row.get("operated_at"))

        return rows

    def list_operation_log_page(
        self,
        db: Session,
        page_num: int,
        page_size: int,
        username: str | None = None,
        method: str | None = None,
        status_code: int | None = None,
        title: str | None = None,
        trace_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """分页查询操作记录。"""
        offset = (page_num - 1) * page_size
        conditions: list[str] = []
        params: dict[str, Any] = {"limit": page_size, "offset": offset}

        if username:
            conditions.append("username ILIKE :username")
            params["username"] = f"%{username}%"
        if method:
            conditions.append("method = :method")
            params["method"] = method.upper()
        if status_code is not None:
            conditions.append("status_code = :status_code")
            params["status_code"] = status_code
        if title:
            conditions.append("title ILIKE :title")
            params["title"] = f"%{title}%"
        if trace_id:
            conditions.append("trace_id = :trace_id")
            params["trace_id"] = trace_id
        if start_time:
            conditions.append("operated_at >= :start_time")
            params["start_time"] = to_utc_datetime(start_time)
        if end_time:
            conditions.append("operated_at <= :end_time")
            params["end_time"] = to_utc_datetime(end_time)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        total_row = fetch_one_in_session(
            db,
            f"SELECT COUNT(*) AS total FROM operation_log {where_sql}",
            params,
        )
        total = int(total_row["total"]) if total_row else 0

        rows = fetch_all_in_session(
            db,
            f"""
            SELECT id, trace_id, user_id, username, method, url, title, status_code, duration_ms, operated_at
            FROM operation_log
            {where_sql}
            ORDER BY operated_at DESC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )


        for row in rows:
            row["operated_at"] = to_iso_string(row.get("operated_at"))

        return rows, total


log_service = LogService()
