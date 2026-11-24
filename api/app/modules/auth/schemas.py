from typing import Literal

from pydantic import BaseModel, Field

from app.modules.user.schemas import UserProfile


class Token(BaseModel):
    """OAuth2 password 登录成功后的令牌响应。"""

    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class LoginResponse(BaseModel):
    """登录响应：未开启 2FA 时直接签发令牌，开启时返回二阶段挑战票据。"""

    requires_2fa: bool = False
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserProfile | None = None
    challenge_token: str | None = None
    challenge_expires_in: int | None = None


class TwoFactorLoginRequest(BaseModel):
    """二阶段 2FA 登录校验请求体。"""

    challenge_token: str = Field(min_length=1, max_length=2048)
    code: str = Field(min_length=1, max_length=32)
    method: Literal["totp", "recovery"] = "totp"
