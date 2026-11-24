# 添加业务模块

以“公告列表”为例。这是扩展教程，公告页面、接口和权限键由新项目实现。编码、API 契约、SQL 与安全细则见 [后端编码规范](backend.md)。

1. **定义接口。** 在 `api/app/modules/announcements/` 写请求与响应模型、路由和服务。在 [API 入口](../api/app/main.py) 注册路由。查询交给服务，通过 [数据库会话](../api/app/db/session.py) 执行参数化 SQL。
2. **定义权限。** 在[权限目录](../api/app/modules/access_control/catalog.py)登记 `announcement.read`，列表接口用 `Depends(require_permission("announcement.read"))` 检查授权。新库从权限目录初始化。已有库通过版本迁移加入权限和所需授权，同时维护 [数据库基线](../api/app/db/init.sql)。
3. **实现页面。** 在 `web/src/api/` 封装公告接口，以[公共请求层](../web/src/utils/request.ts)处理响应。在 `web/src/view/announcements/index.vue` 按 [UI 规范](ui.md)复用表格列表骨架。
4. **注册菜单。** 在菜单管理选择前端组件 `view/announcements/index.vue`。动态路由通过[组件映射](../web/src/router/component-map.ts)加载页面。给目标用户组分配菜单和 `announcement.read`，分别确认入口和 API 行为。
5. **验证。** 用有权限和无权限的普通账号验证页面访问、分页和操作结果。确认直接请求接口也遵循授权。数据库有结构或种子变化时，分别验证空库初始化与已有库升级。

菜单授权决定用户能看到哪些页面入口，操作权限决定 API 能做什么。后端权限变更与前端入口应一同验证。
