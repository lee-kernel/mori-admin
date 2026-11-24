"""用户双因素认证（TOTP + 一次性恢复码）业务服务。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.totp import (
    build_otpauth_uri,
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_recovery_codes,
    generate_totp_secret,
    hash_recovery_code,
    verify_recovery_code,
    verify_totp_code,
)
from app.db.session import execute_in_session, fetch_all_in_session, fetch_one_in_session
from app.utils.datetime import to_iso_string

logger = logging.getLogger("app")


class TwoFactorError(ValueError):
    """2FA 业务校验失败（由路由层映射为具体 HTTP 状态码）。"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TotpService:
    """封装 TOTP 绑定、验证、恢复码与重置的数据访问逻辑。"""

    def get_status(self, db: Session, user_id: int) -> dict[str, Any]:
        row = fetch_one_in_session(
            db,
            """
            SELECT enabled, enabled_at
            FROM user_totp
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        enabled = bool(row and row.get("enabled"))
        remaining = 0
        if enabled:
            count_row = fetch_one_in_session(
                db,
                """
                SELECT COUNT(*) AS remaining
                FROM user_totp_recovery_code
                WHERE user_id = :user_id AND used_at IS NULL
                """,
                {"user_id": user_id},
            )
            remaining = int(count_row["remaining"]) if count_row else 0
        return {
            "enabled": enabled,
            "enabled_at": to_iso_string(row.get("enabled_at")) if enabled and row else None,
            "recovery_codes_remaining": remaining,
        }

    def start_setup(self, db: Session, user_id: int, username: str) -> dict[str, Any]:
        """生成待确认的 TOTP 密钥与 otpauth URI，不改变当前生效状态。"""
        existing = fetch_one_in_session(
            db,
            "SELECT enabled FROM user_totp WHERE user_id = :user_id",
            {"user_id": user_id},
        )
        if existing and existing.get("enabled"):
            raise TwoFactorError("双因素认证已开启", status_code=409)

        secret = generate_totp_secret()
        encrypted = encrypt_totp_secret(secret)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.TOTP_SETUP_EXPIRE_SECONDS)

        execute_in_session(
            db,
            """
            INSERT INTO user_totp (user_id, pending_secret_encrypted, pending_expires_at, enabled)
            VALUES (:user_id, :pending_secret_encrypted, :pending_expires_at, FALSE)
            ON CONFLICT (user_id) DO UPDATE SET
                pending_secret_encrypted = EXCLUDED.pending_secret_encrypted,
                pending_expires_at = EXCLUDED.pending_expires_at
            """,
            {
                "user_id": user_id,
                "pending_secret_encrypted": encrypted,
                "pending_expires_at": expires_at,
            },
        )
        return {
            "otpauth_uri": build_otpauth_uri(secret, username),
            "manual_key": secret,
            "expires_in": settings.TOTP_SETUP_EXPIRE_SECONDS,
        }

    def _replace_recovery_codes_in_tx(self, db: Session, user_id: int) -> list[str]:
        codes = generate_recovery_codes()
        execute_in_session(
            db,
            "DELETE FROM user_totp_recovery_code WHERE user_id = :user_id",
            {"user_id": user_id},
            commit=False,
        )
        for code in codes:
            execute_in_session(
                db,
                """
                INSERT INTO user_totp_recovery_code (user_id, code_hash)
                VALUES (:user_id, :code_hash)
                """,
                {
                    "user_id": user_id,
                    "code_hash": hash_recovery_code(code),
                },
                commit=False,
            )
        return codes

    def enable(self, db: Session, user_id: int, code: str) -> list[str]:
        """校验待确认 TOTP 码后正式启用 2FA，并一次性生成恢复码。"""
        row = fetch_one_in_session(
            db,
            """
            SELECT enabled, pending_secret_encrypted, pending_expires_at
            FROM user_totp
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        if not row or not row.get("pending_secret_encrypted"):
            raise TwoFactorError("请先发起双因素认证绑定", status_code=400)
        if row.get("enabled"):
            raise TwoFactorError("双因素认证已开启", status_code=409)

        expires_at = row.get("pending_expires_at")
        now = datetime.now(timezone.utc)
        if not expires_at or (expires_at.tzinfo is None and expires_at.replace(tzinfo=timezone.utc) <= now) or (expires_at.tzinfo is not None and expires_at <= now):
            raise TwoFactorError("绑定二维码已过期，请重新生成", status_code=400)

        secret = decrypt_totp_secret(row["pending_secret_encrypted"])
        matched_step = verify_totp_code(secret, code)
        if matched_step is None:
            raise TwoFactorError("动态验证码无效或已过期，请重试", status_code=400)

        try:
            execute_in_session(
                db,
                """
                UPDATE user_totp
                SET secret_encrypted = pending_secret_encrypted,
                    pending_secret_encrypted = NULL,
                    pending_expires_at = NULL,
                    enabled = TRUE,
                    last_used_step = :matched_step,
                    enabled_at = :enabled_at
                WHERE user_id = :user_id
                """,
                {
                    "user_id": user_id,
                    "matched_step": matched_step,
                    "enabled_at": now,
                },
                commit=False,
            )
            recovery_codes = self._replace_recovery_codes_in_tx(db, user_id)
            db.commit()
        except Exception:
            db.rollback()
            raise

        logger.info("用户已开启双因素认证 | 用户ID=%s", user_id)
        return recovery_codes

    def verify_active_code(
        self,
        db: Session,
        user_id: int,
        code: str,
        method: Literal["totp", "recovery"] = "totp",
        *,
        commit: bool = True,
    ) -> bool:
        """校验已启用 2FA 的动态码或一次性恢复码，并防重放/防双花。"""
        row = fetch_one_in_session(
            db,
            """
            SELECT enabled, secret_encrypted, last_used_step
            FROM user_totp
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        if not row or not row.get("enabled") or not row.get("secret_encrypted"):
            return False

        if method == "totp":
            secret = decrypt_totp_secret(row["secret_encrypted"])
            matched_step = verify_totp_code(
                secret,
                code,
                last_used_step=row.get("last_used_step"),
            )
            if matched_step is None:
                return False
            affected = execute_in_session(
                db,
                """
                UPDATE user_totp
                SET last_used_step = :matched_step
                WHERE user_id = :user_id
                  AND enabled IS TRUE
                  AND (last_used_step IS NULL OR last_used_step < :matched_step)
                """,
                {
                    "user_id": user_id,
                    "matched_step": matched_step,
                },
                commit=commit,
            )
            return affected > 0

        if method == "recovery":
            candidates = fetch_all_in_session(
                db,
                """
                SELECT id, code_hash
                FROM user_totp_recovery_code
                WHERE user_id = :user_id AND used_at IS NULL
                ORDER BY id
                """,
                {"user_id": user_id},
            )
            matched_id: int | None = None
            for item in candidates:
                if verify_recovery_code(code, item["code_hash"]):
                    matched_id = int(item["id"])
                    break
            if matched_id is None:
                return False
            affected = execute_in_session(
                db,
                """
                UPDATE user_totp_recovery_code
                SET used_at = :used_at
                WHERE id = :id AND used_at IS NULL
                """,
                {
                    "id": matched_id,
                    "used_at": datetime.now(timezone.utc),
                },
                commit=commit,
            )
            return affected > 0

        return False

    def disable(
        self,
        db: Session,
        user_id: int,
        code: str,
        method: Literal["totp", "recovery"] = "totp",
    ) -> None:
        """校验 2FA 码后关闭双因素认证，清理密钥与恢复码并递增令牌版本。"""
        try:
            if not self.verify_active_code(db, user_id, code, method, commit=False):
                db.rollback()
                raise TwoFactorError("验证码或恢复码无效", status_code=400)
            self._clear_totp_in_tx(db, user_id)
            db.commit()
        except TwoFactorError:
            raise
        except Exception:
            db.rollback()
            raise
        logger.info("用户已关闭双因素认证，历史令牌已撤销 | 用户ID=%s", user_id)

    def regenerate_recovery_codes(self, db: Session, user_id: int, code: str) -> list[str]:
        """校验当前 TOTP 码后重新生成一次性恢复码。"""
        try:
            if not self.verify_active_code(db, user_id, code, "totp", commit=False):
                db.rollback()
                raise TwoFactorError("动态验证码无效或已过期", status_code=400)
            codes = self._replace_recovery_codes_in_tx(db, user_id)
            db.commit()
        except TwoFactorError:
            raise
        except Exception:
            db.rollback()
            raise
        logger.info("用户已重新生成 2FA 恢复码 | 用户ID=%s", user_id)
        return codes

    def admin_reset(self, db: Session, user_id: int) -> None:
        """管理员紧急解绑用户 2FA 并撤销其历史令牌。"""
        try:
            self._clear_totp_in_tx(db, user_id)
            db.commit()
        except Exception:
            db.rollback()
            raise
        logger.warning("管理员已重置用户双因素认证，历史令牌已撤销 | 目标用户ID=%s", user_id)

    def _clear_totp_in_tx(self, db: Session, user_id: int) -> None:
        execute_in_session(
            db,
            "DELETE FROM user_totp_recovery_code WHERE user_id = :user_id",
            {"user_id": user_id},
            commit=False,
        )
        execute_in_session(
            db,
            "DELETE FROM user_totp WHERE user_id = :user_id",
            {"user_id": user_id},
            commit=False,
        )
        execute_in_session(
            db,
            'UPDATE "user" SET token_version = token_version + 1 WHERE id = :user_id',
            {"user_id": user_id},
            commit=False,
        )


totp_service = TotpService()
