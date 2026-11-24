import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_2fa_challenge_token,
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import LoginResponse, Token, TwoFactorLoginRequest
from app.modules.audit.service.log_service import log_service
from app.modules.user.schemas import UserProfile
from app.modules.user.service.totp_service import totp_service
from app.modules.user.service.user_service import user_service
from app.schemas.response import ApiResponse
from app.utils.response import success


router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app")


def _get_client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _parse_user_agent(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent", "").strip()
    if not user_agent:
        return None, None

    platform = "Unknown"
    platform_markers = (
        ("Windows", "Windows"),
        ("Mac OS X", "macOS"),
        ("Android", "Android"),
        ("iPhone", "iOS"),
        ("iPad", "iOS"),
        ("Linux", "Linux"),
    )
    for marker, label in platform_markers:
        if marker in user_agent:
            platform = label
            break

    browser = "Unknown"
    browser_markers = (
        ("Edg/", "Edge"),
        ("Chrome/", "Chrome"),
        ("Firefox/", "Firefox"),
        ("Safari/", "Safari"),
    )
    for marker, label in browser_markers:
        if marker in user_agent:
            browser = label
            break

    return platform, browser


def _issue_login_token(
    request: Request,
    db: Session,
    user: dict[str, Any],
    auth_method: str,
) -> Token:
    """记录登录信息并签发 token。"""
    ip_address = _get_client_ip(request)
    platform, browser = _parse_user_agent(request)

    user_service.record_login(
        db,
        user["id"],
        datetime.now(timezone.utc),
        ip_address,
    )

    try:
        log_service.create_login_log(
            db,
            user_id=user["id"],
            username=user["username"],
            ip_address=ip_address,
            platform=platform,
            browser=browser,
            login_at=datetime.now(timezone.utc),
        )
    except Exception:
        # 审计日志不是登录主流程；写入失败时必须回滚，否则后续查询会收到
        # PostgreSQL InFailedSqlTransaction 并把本应成功的登录变成 500。
        db.rollback()
        logger.exception("登录审计日志写入失败 | 用户ID=%s", user["id"])

    fresh_user = user_service.get_by_id(db, user["id"])
    user_profile = UserProfile(**fresh_user)
    logger.info(
        "用户登录成功 | 用户=%s | 用户ID=%s | 认证方式=%s | IP=%s",
        fresh_user["username"],
        fresh_user["id"],
        auth_method,
        ip_address or "-",
    )
    return Token(
        access_token=create_access_token(
            subject=fresh_user["username"],
            user_id=int(fresh_user["id"]),
            token_version=int(fresh_user.get("token_version", 0)),
        ),
        user=user_profile,
    )


@router.post("/logout", response_model=ApiResponse[None])
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> ApiResponse[None]:
    """退出登录并记录日志。"""
    ip_address = _get_client_ip(request)
    platform, browser = _parse_user_agent(request)

    # 记录退出日志 (event_type=2)
    try:
        log_service.create_login_log(
            db,
            user_id=current_user.id,
            username=current_user.username,
            ip_address=ip_address,
            platform=platform,
            browser=browser,
            event_type=2,
            login_at=datetime.now(timezone.utc),
        )
    except Exception:
        db.rollback()
        logger.exception("退出审计日志写入失败 | 用户ID=%s", current_user.id)

    user_service.revoke_tokens(db, current_user.id)
    logger.info(
        "用户退出登录，历史令牌已撤销 | 用户=%s | 用户ID=%s | IP=%s",
        current_user.username,
        current_user.id,
        ip_address or "-",
    )

    return success(None, message="logout success")


@router.post("/login", response_model=ApiResponse[LoginResponse])
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> ApiResponse[LoginResponse]:
    """使用 OAuth2 Password 表单登录；已开启 2FA 时返回短期挑战票据。"""
    user = user_service.get_by_username(db, form_data.username)
    if user and user_service.is_password_login_locked(user):
        logger.warning(
            "密码登录被临时锁定 | 用户=%s | 用户ID=%s | IP=%s",
            user["username"],
            user["id"],
            _get_client_ip(request) or "-",
        )
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "账户暂时锁定，请稍后再试")
    if not user or not verify_password(form_data.password, user.get("hashed_password")):
        if user:
            user_service.record_password_login_failure(db, user["id"])
        logger.warning(
            "密码登录失败 | 用户=%s | 用户存在=%s | IP=%s",
            form_data.username,
            bool(user),
            _get_client_ip(request) or "-",
        )

        # 登录失败也记录日志
        ip_address = _get_client_ip(request)
        platform, browser = _parse_user_agent(request)
        try:
            log_service.create_login_log(
                db,
                user_id=user["id"] if user else None,
                username=form_data.username[:64],
                ip_address=ip_address,
                platform=platform,
                browser=browser,
                login_at=datetime.now(timezone.utc),
                event_type=3,
            )
        except Exception:
            db.rollback()
            logger.exception("登录失败审计日志写入失败 | 用户=%s", form_data.username)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")

    if not user.get("is_active"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "用户已被禁用")

    if user.get("totp_enabled"):
        challenge_token = create_2fa_challenge_token(
            subject=user["username"],
            user_id=int(user["id"]),
            token_version=int(user.get("token_version", 0)),
        )
        return success(
            LoginResponse(
                requires_2fa=True,
                challenge_token=challenge_token,
                challenge_expires_in=settings.TOTP_CHALLENGE_EXPIRE_SECONDS,
            )
        )

    user_service.reset_password_login_failures(db, user["id"])
    token = _issue_login_token(request, db, user, auth_method="密码")
    return success(
        LoginResponse(
            requires_2fa=False,
            access_token=token.access_token,
            token_type=token.token_type,
            user=token.user,
        )
    )


@router.post("/login/2fa", response_model=ApiResponse[Token])
def login_verify_2fa(
    request: Request,
    payload_in: TwoFactorLoginRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[Token]:
    """二阶段 2FA 登录校验：支持 6 位 TOTP 动态码与一次性恢复码。"""
    token_payload = decode_access_token(payload_in.challenge_token)
    if not token_payload or token_payload.get("purpose") != "2fa_login":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "验证会话已过期，请重新登录")

    username = token_payload.get("sub")
    user_id = token_payload.get("uid")
    if not username or not isinstance(user_id, int) or user_id <= 0:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "验证会话无效，请重新登录")

    user = user_service.get_by_username(db, username)
    if not user or int(user["id"]) != user_id or not user.get("is_active"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在或已被禁用")
    if int(token_payload.get("ver", -1)) != int(user.get("token_version", 0)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "验证会话已失效，请重新登录")
    if not user.get("totp_enabled"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "当前账号未开启双因素认证")
    if user_service.is_password_login_locked(user):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "账户暂时锁定，请稍后再试")

    verified = totp_service.verify_active_code(
        db,
        user["id"],
        payload_in.code,
        payload_in.method,
    )
    if not verified:
        user_service.record_password_login_failure(db, user["id"])
        ip_address = _get_client_ip(request)
        platform, browser = _parse_user_agent(request)
        logger.warning(
            "2FA 登录验证失败 | 用户=%s | 用户ID=%s | 方式=%s | IP=%s",
            user["username"],
            user["id"],
            payload_in.method,
            ip_address or "-",
        )
        try:
            log_service.create_login_log(
                db,
                user_id=user["id"],
                username=user["username"],
                ip_address=ip_address,
                platform=platform,
                browser=browser,
                login_at=datetime.now(timezone.utc),
                event_type=3,
            )
        except Exception:
            db.rollback()
            logger.exception("2FA 登录失败审计日志写入失败 | 用户ID=%s", user["id"])
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "动态验证码无效或已过期" if payload_in.method == "totp" else "恢复码无效或已被使用",
        )

    user_service.reset_password_login_failures(db, user["id"])
    auth_method = "密码+2FA" if payload_in.method == "totp" else "密码+2FA恢复码"
    return success(_issue_login_token(request, db, user, auth_method=auth_method))
