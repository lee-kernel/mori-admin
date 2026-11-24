import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def digest_password_for_transport(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_password_hash(password_digest: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_digest.encode("utf-8"),
        salt.encode("utf-8"),
        settings.PASSWORD_HASH_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${settings.PASSWORD_HASH_ITERATIONS}${salt}${digest}"


def verify_password(password_digest: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False

    try:
        algorithm, iterations, salt, stored_digest = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_digest.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, stored_digest)


def create_access_token(
    subject: str,
    user_id: int,
    token_version: int,
    expires_delta: timedelta | None = None,
    purpose: str = "access",
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "uid": user_id,
        "ver": token_version,
        "purpose": purpose,
        "exp": int(expire.timestamp()),
    }

    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def create_2fa_challenge_token(
    subject: str,
    user_id: int,
    token_version: int,
) -> str:
    """签发仅用于完成登录 2FA 校验的短期临时票据。"""
    return create_access_token(
        subject=subject,
        user_id=user_id,
        token_version=token_version,
        expires_delta=timedelta(seconds=settings.TOTP_CHALLENGE_EXPIRE_SECONDS),
        purpose="2fa_login",
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        actual_signature = _b64url_decode(signature_part)
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None

        payload = json.loads(_b64url_decode(payload_part))
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return payload
    except (ValueError, json.JSONDecodeError, TypeError):
        return None
