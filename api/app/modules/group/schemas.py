from pydantic import BaseModel, Field


class GroupBase(BaseModel):
    """用户组基础字段，CRUD 共用。"""

    name: str = Field(min_length=1, max_length=64)
    description: str | None = None
    # 用户组可访问的菜单 id 列表
    menu_ids: list[int] = Field(default_factory=list)
    permission_keys: list[str] = Field(default_factory=list, description="此用户组拥有的操作权限键")


class GroupCreate(GroupBase):
    pass


class GroupUpdate(GroupBase):
    pass


class GroupProfile(GroupBase):
    id: int
    is_system: bool = False
    is_admin: bool = False


class GroupPage(BaseModel):
    list: list[GroupProfile]
    total: int


class GroupOptions(BaseModel):
    """用户组下拉数据：可选用户组 + 可用菜单列表（扁平）。"""

    groups: list[GroupProfile]
