"""标准 TOTP (RFC 6238)、密钥加密存储与一次性恢复码工具。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

TOTP_PERIOD_SECONDS = 30
TOTP_DIGITS = 6
RECOVERY_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
RECOVERY_CODE_COUNT = 8
RECOVERY_CODE_HASH_ITERATIONS = 100_000


def _get_fernet() -> Fernet:
    configured = settings.TOTP_ENCRYPTION_KEY.strip()
    if configured:
        return Fernet(configured.encode("ascii"))
    derived = hashlib.sha256(f"mori-admin:totp:{settings.SECRET_KEY}".encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def generate_totp_secret() -> str:
    """生成 160-bit 随机密钥并编码为不带填充的 Base32 字符串。"""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def encrypt_totp_secret(secret: str) -> str:
    return _get_fernet().encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_totp_secret(encrypted: str) -> str:
    try:
        return _get_fernet().decrypt(encrypted.encode("ascii")).decode("ascii")
    except InvalidToken as exc:
        raise ValueError("无法解密 2FA 密钥，请检查加密密钥配置") from exc


def build_otpauth_uri(secret: str, username: str, issuer: str | None = None) -> str:
    resolved_issuer = (issuer or settings.TOTP_ISSUER).strip() or "Mori Admin"
    label = f"{quote(resolved_issuer)}:{quote(username)}"
    return (
        f"otpauth://totp/{label}"
        f"?secret={quote(secret)}"
        f"&issuer={quote(resolved_issuer)}"
        f"&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_PERIOD_SECONDS}"
    )


def _decode_base32_secret(secret: str) -> bytes:
    cleaned = secret.strip().replace(" ", "").upper()
    padding = "=" * (-len(cleaned) % 8)
    return base64.b32decode(cleaned + padding, casefold=True)


def generate_totp_code(secret: str, step: int) -> str:
    key = _decode_base32_secret(secret)
    msg = struct.pack(">Q", step)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**TOTP_DIGITS)
    return str(code_int).zfill(TOTP_DIGITS)


def normalize_totp_code(code: str) -> str:
    return "".join(ch for ch in code if ch.isdigit())


def verify_totp_code(
    secret: str,
    code: str,
    *,
    current_time: float | None = None,
    valid_window: int = 1,
    last_used_step: int | None = None,
) -> int | None:
    """校验 6 位 TOTP 码；通过时返回匹配时间步，失败或重放时返回 None。"""
    normalized = normalize_totp_code(code)
    if len(normalized) != TOTP_DIGITS:
        return None

    now = time.time() if current_time is None else current_time
    current_step = int(now // TOTP_PERIOD_SECONDS)
    for delta in range(-valid_window, valid_window + 1):
        step = current_step + delta
        if step < 0:
            continue
        if last_used_step is not None and step <= last_used_step:
            continue
        expected = generate_totp_code(secret, step)
        if hmac.compare_digest(expected, normalized):
            return step
    return None


def generate_recovery_codes(count: int = RECOVERY_CODE_COUNT) -> list[str]:
    """生成易读的一次性恢复码（格式：XXXX-XXXX）。"""
    codes: list[str] = []
    for _ in range(count):
        raw = "".join(secrets.choice(RECOVERY_CODE_ALPHABET) for _ in range(8))
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def normalize_recovery_code(code: str) -> str:
    return "".join(ch for ch in code.upper() if ch.isalnum())


def hash_recovery_code(code: str) -> str:
    normalized = normalize_recovery_code(code)
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized.encode("utf-8"),
        salt.encode("utf-8"),
        RECOVERY_CODE_HASH_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${RECOVERY_CODE_HASH_ITERATIONS}${salt}${digest}"


def verify_recovery_code(code: str, stored_hash: str) -> bool:
    normalized = normalize_recovery_code(code)
    if len(normalized) != 8:
        return False
    try:
        algorithm, iterations, salt, stored_digest = stored_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, stored_digest)
