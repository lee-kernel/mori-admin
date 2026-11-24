# Mori 工程入口（AI Agent UI 约束框架）

本文件适用于整个仓库。Mori 的核心目标是**让 AI Agent 在开发页面时稳定产出一致、可靠、深浅色与窄屏都可用的 UI**；仓库同时内置一套可选的 FastAPI + PostgreSQL 后台底座作为全栈参考。先按任务查 [文档索引](docs/README.md)，再阅读对应源码。保留用户已有修改。

## 核心原则

1. **不引入额外 UI 框架**：严格使用项目既有的 Vue 3、TypeScript、Ant Design Vue（已在 `web/src/main.ts` 注册的组件）与仓库公共布局组件，禁止引入 Tailwind、Element Plus、Naive UI 或其他 UI/CSS/图标框架。
2. **先抄范例，再填业务**：写新页面前，先读 [页面生成流程](docs/ai-page-workflow.md) 和 [UI 规范](docs/ui.md)，从表格、卡片、详情、工作台、表单或弹窗/抽屉中选一个最接近的真实页面作为参考。
3. **布局与主题全部走框架原语**：业务页面根节点必须是 `PageLayout`；颜色一律使用 `--ant-*` 或 `--mori-admin-*` 主题 Token，禁止硬编码色值与手写 `100vh` / `100dvh`。

## 生成或修改页面

1. 若仅需验证 UI 而不启动后端/数据库，在 `web/` 下运行 `npm run dev:preview` 进入纯前端 UI 预览模式。
2. 接口类型放在 `web/src/api/`，请求统一经过 `web/src/utils/request.ts`；如需接入内置全栈底座，按后端动态菜单注册组件，操作权限由后端判断。
3. 提交前必须通过以下门禁：
   - `npm run typecheck`（TypeScript / Vue 模板类型检查）
   - `npm run check:ui`（UI 静态门禁：禁止额外 UI 框架、校验 `<a-*>` 注册、校验 `PageLayout` 根节点、禁止硬编码色值与 `100vh`）
   - 改动文件的 ESLint 与 Prettier 检查（`npm run lint`）
   - 涉及 UI 布局改动时，运行 `npm run verify:ui -- /你的路由` 自动检查桌面/窄屏 × 浅色/深色下的渲染与横向溢出（可加 `--screenshots` 输出截图核对）
   - 涉及路由、构建或公共组件时再运行 `npm run build`

## 修改后端（可选全栈底座）

先读局部入口 [api/AGENTS.md](api/AGENTS.md)，遵循 [后端编码规范](docs/backend.md) 与 [模块开发指南](docs/module-development.md)。路由负责协议和鉴权、严禁写 SQL；服务负责业务和参数化 SQL（统一经 `app/db/session.py`）；多步写入共享同一事务。数据库变更同步维护新库基线和已有数据库的版本迁移，保留已发布迁移。只验证本次改动直接涉及的行为。

## 维护文档

项目规则尽量只在一处详细说明，由入口文档链接。更新组件、路由或 API 契约时同步更新对应指南。纯文档改动核对链接、标题和源码依据即可。交付时说明实际验证范围，浏览器检查只在确实操作过或跑过 `verify:ui` 时记为通过。
