from collections.abc import Generator, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
import logging
import re
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from psycopg.types.json import Jsonb

from app.core.config import settings
from app.core.logging import exception_diagnostics

logger = logging.getLogger("app")
_commit_state: ContextVar[dict | None] = ContextVar("db_commit_diagnostics", default=None)


def _log_database_failure(stage: str, exc: BaseException) -> None:
    """仅输出异常类型和经过格式校验的 SQLSTATE，不输出 SQL 或异常原文。"""
    code = getattr(getattr(exc, "orig", exc), "sqlstate", None)
    sqlstate = code if isinstance(code, str) and re.fullmatch(r"[0-9A-Z]{5}", code) else "-"
    logger.error("数据库操作失败 | 阶段=%s | 异常链=%s | SQLSTATE=%s", stage, exception_diagnostics(exc), sqlstate)


def _register_database_diagnostics(target: Engine) -> None:
    @event.listens_for(target, "handle_error")
    def on_error(context):
        state = _commit_state.get()
        stage = "连接" if context.connection is None else "提交" if state is not None else "执行" if context.statement is not None else "连接"
        if state is not None:
            state["logged"] = True
        _log_database_failure(stage, context.sqlalchemy_exception or context.original_exception)


class DiagnosticSession(Session):
    """为直接提交提供失败诊断，保持 SQLAlchemy 的异常和事务语义。"""

    def commit(self) -> None:
        state = {"logged": False}
        token = _commit_state.set(state)
        try:
            super().commit()
        except SQLAlchemyError as exc:
            if not state["logged"]:
                _log_database_failure("提交", exc)
            raise
        finally:
            _commit_state.reset(token)

SqlParams = dict[str, Any] | None

# 统一的 SQL 参数类型，便于直接执行文本 SQL 时复用。


def jsonb_param(value: Any) -> Jsonb:
    """将 Python 结构显式标记为 PostgreSQL JSONB 参数。"""
    return Jsonb(value)


def _build_engine() -> Engine:
    """创建数据库引擎，连接池参数统一从配置读取。"""
    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        hide_parameters=True,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )


engine = _build_engine()
_register_database_diagnostics(engine)


@event.listens_for(engine, "connect")
def _set_postgresql_session_timezone(dbapi_connection: Any, _connection_record: Any) -> None:
    """固定 PostgreSQL 会话为 UTC，使 TIMESTAMPTZ 的展示不依赖部署主机。"""
    if engine.dialect.name != "postgresql":
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET TIME ZONE 'UTC'")
    finally:
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=DiagnosticSession)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：为每个请求提供数据库会话并在结束后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def pinned_session() -> Iterator[Session]:
    """提供绑定到同一物理连接的会话，供会话级 advisory lock 使用。"""
    with engine.connect() as connection:
        with DiagnosticSession(bind=connection, autoflush=False, expire_on_commit=False) as db:
            yield db


def execute(sql: str, params: SqlParams = None) -> int:
    """执行写入类 SQL，并返回受影响行数。"""
    with SessionLocal() as db:
        result = db.execute(text(sql), params or {})
        db.commit()
        return result.rowcount


def fetch_one(sql: str, params: SqlParams = None) -> dict[str, Any] | None:
    """查询单行数据，未命中时返回 None。"""
    with SessionLocal() as db:
        result = db.execute(text(sql), params or {}).mappings().first()
        return dict(result) if result else None


def fetch_all(sql: str, params: SqlParams = None) -> list[dict[str, Any]]:
    """查询多行数据，并转换为普通字典列表。"""
    with SessionLocal() as db:
        result = db.execute(text(sql), params or {}).mappings().all()
        return [dict(row) for row in result]


def execute_in_session(
    db: Session, sql: str, params: SqlParams = None, *, commit: bool = True
) -> int:
    """在外部传入的会话中执行写入类 SQL，可由调用方控制事务提交。"""
    result = db.execute(text(sql), params or {})
    if commit:
        db.commit()
    return result.rowcount


def execute_returning_one_in_session(
    db: Session, sql: str, params: SqlParams = None, *, commit: bool = True
) -> dict[str, Any] | None:
    """执行带 ``RETURNING`` 的写语句，原子返回单行并按需提交。"""
    result = db.execute(text(sql), params or {})
    row = result.mappings().first()
    if commit:
        db.commit()
    return dict(row) if row else None


def execute_returning_all_in_session(
    db: Session, sql: str, params: SqlParams = None, *, commit: bool = True
) -> list[dict[str, Any]]:
    """执行带 ``RETURNING`` 的批量写语句，读取全部结果后按需提交。"""
    result = db.execute(text(sql), params or {})
    rows = [dict(row) for row in result.mappings().all()]
    if commit:
        db.commit()
    return rows


def insert_in_session(
    db: Session, sql: str, params: SqlParams = None, *, commit: bool = True
) -> int:
    """执行带显式 ``RETURNING id`` 的 INSERT 并返回 identity 主键。"""
    statement = sql.rstrip().removesuffix(";")
    if not re.search(r"\bRETURNING\s+id\b", statement, flags=re.IGNORECASE):
        raise ValueError("INSERT SQL 必须显式包含 RETURNING id")
    result = db.execute(text(statement), params or {})
    try:
        inserted_id = result.scalar_one()
    except NoResultFound as exc:
        raise RuntimeError("INSERT ... RETURNING id 未返回主键") from exc
    if inserted_id is None:
        raise RuntimeError("INSERT ... RETURNING id 返回了空主键")
    if commit:
        db.commit()
    return int(inserted_id)


def fetch_one_in_session(db: Session, sql: str, params: SqlParams = None) -> dict[str, Any] | None:
    """在外部传入的会话中查询单行数据。"""
    result = db.execute(text(sql), params or {}).mappings().first()
    return dict(result) if result else None


def fetch_all_in_session(db: Session, sql: str, params: SqlParams = None) -> list[dict[str, Any]]:
    """在外部传入的会话中查询多行数据。"""
    result = db.execute(text(sql), params or {}).mappings().all()
    return [dict(row) for row in result]
