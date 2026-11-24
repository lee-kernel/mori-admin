"""管理员和业务模块共用的稳定操作权限定义。"""

from dataclasses import dataclass
from typing import Literal

Operation = Literal["read", "create", "edit", "delete", "run", "manage"]


@dataclass(frozen=True)
class Permission:
    key: str
    label: str
    domain: str
    operation: Operation
    high_risk: bool = False


_OPERATIONS: tuple[tuple[Operation, str], ...] = (
    ("read", "查看"), ("create", "创建"), ("edit", "编辑"), ("delete", "删除"),
)
OPERATION_LABELS = dict(_OPERATIONS) | {"run": "运行", "manage": "管理"}

DOMAIN_LABELS = {
    "user": "用户",
    "group": "用户组",
    "menu": "菜单",
    "branding": "品牌设置",
    "audit_login": "登录日志",
    "audit_operation": "操作日志",
}
_DOMAIN_OPERATIONS = {
    "user": ("read", "create", "edit", "delete"),
    "group": ("read", "create", "edit", "delete"),
    "menu": ("read", "create", "edit", "delete"),
    "branding": ("edit",),
    "audit_login": ("read",),
    "audit_operation": ("read",),
}
PERMISSIONS: dict[str, Permission] = {
    f"{domain}.{operation}": Permission(
        f"{domain}.{operation}", f"{DOMAIN_LABELS[domain]}·{OPERATION_LABELS[operation]}",
        domain, operation, high_risk=operation in {"delete", "run"},
    )
    for domain, operations in _DOMAIN_OPERATIONS.items() for operation in operations
}

def get_permission(key: str) -> Permission | None:
    """未知权限默认无效。"""
    return PERMISSIONS.get(key)
