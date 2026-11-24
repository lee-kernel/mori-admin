from __future__ import annotations

from pydantic import BaseModel, Field


class MenuBase(BaseModel):
    """菜单基础字段，CRUD 共用。"""

    parent_id: int | None = None
    name: str = Field(min_length=1, max_length=64)
    path: str = Field(min_length=1, max_length=128)
    permission_key: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9][a-z0-9:_-]*$")
    component: str | None = Field(default=None, max_length=128)
    icon: str | None = Field(default=None, max_length=64)
    redirect: str | None = Field(default=None, max_length=128)
    sort: int = 0
    hidden: bool = False
    is_external: bool = False


class MenuCreate(MenuBase):
    pass


class MenuUpdate(MenuBase):
    pass


class MenuItem(MenuBase):
    """菜单展示模型，附带系统标识与时间戳。"""

    id: int
    is_system: bool = False


class MenuNode(MenuItem):
    """树形菜单节点。"""

    children: list["MenuNode"] = Field(default_factory=list)


MenuNode.model_rebuild()


class MenuList(BaseModel):
    list: list[MenuItem]


class MenuTree(BaseModel):
    list: list[MenuNode]
