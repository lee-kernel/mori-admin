from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用户基础字段，创建和展示模型共用。"""

    username: str
    display_name: str
    email: EmailStr | None = None
    is_active: bool = True
    group_id: int | None = None
    last_login_at: str | None = None
    last_login_ip: str | None = None


class UserCreate(UserBase):
    """创建用户请求体。"""

    password: str


class UserUpdate(BaseModel):
    """修改用户请求体。"""

    display_name: str
    email: EmailStr | None = None
    is_active: bool = True
    group_id: int | None = None


class UserPasswordUpdate(BaseModel):
    """管理员重置用户密码请求体。"""

    password: str = Field(min_length=6)


class CurrentUserProfileUpdate(BaseModel):
    """当前用户可修改的资料字段。"""

    display_name: str = Field(min_length=1, max_length=128)
    email: EmailStr | None = None


class CurrentUserPasswordUpdate(BaseModel):
    """当前用户修改密码请求体，密码值为前端传输摘要。"""

    current_password: str = Field(min_length=64, max_length=64)
    new_password: str = Field(min_length=64, max_length=64)


class UserProfile(UserBase):
    """用户资料响应体，包含当前角色拥有的菜单及稳定权限标识。"""

    id: int
    group_name: str | None = None
    is_admin: bool = False
    totp_enabled: bool = False
    menu_ids: list[int] = Field(default_factory=list)
    menu_paths: list[str] = Field(default_factory=list)
    operation_permission_keys: list[str] = Field(default_factory=list)


class UserPage(BaseModel):
    """用户分页响应体。"""

    list: list[UserProfile]
    total: int


class TwoFactorStatusResponse(BaseModel):
    """当前用户 2FA 状态。"""

    enabled: bool = False
    enabled_at: str | None = None
    recovery_codes_remaining: int = 0


class TwoFactorSetupRequest(BaseModel):
    """发起 2FA 绑定前需校验当前密码摘要。"""

    current_password: str = Field(min_length=64, max_length=64)


class TwoFactorSetupResponse(BaseModel):
    """2FA 绑定二维码信息。"""

    otpauth_uri: str
    manual_key: str
    expires_in: int


class TwoFactorEnableRequest(BaseModel):
    """确认开启 2FA 请求体。"""

    code: str = Field(min_length=6, max_length=16)


class TwoFactorRecoveryCodesResponse(BaseModel):
    """一次性恢复码响应（仅创建/重置时返回一次）。"""

    recovery_codes: list[str]


class TwoFactorDisableRequest(BaseModel):
    """关闭 2FA 请求体。"""

    current_password: str = Field(min_length=64, max_length=64)
    code: str = Field(min_length=1, max_length=32)
    method: Literal["totp", "recovery"] = "totp"


class TwoFactorRegenerateRequest(BaseModel):
    """重新生成 2FA 恢复码请求体。"""

    current_password: str = Field(min_length=64, max_length=64)
    code: str = Field(min_length=6, max_length=16)
