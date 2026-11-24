# Mori

[![Vue 3.5](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Ant Design Vue 4.2](https://img.shields.io/badge/Ant%20Design%20Vue-4.2-1677FF?logo=antdesign&logoColor=white)](https://antdv.com/)
[![TypeScript 5.9](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite 5.4](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![Node.js 22](https://img.shields.io/badge/Node.js-22-5FA04E?logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![FastAPI 0.115](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

Mori 是一套基于 Vue 3 + Ant Design Vue 的后台前端工程，用来约束 AI Agent 写页面时的布局、组件和样式，避免每次生成都跑偏或临时引入其他 UI 库。仓库里也附带了一套可选的 FastAPI + PostgreSQL 后台（登录、可选 2FA、用户组、动态菜单、操作权限和审计日志）。

## 仓库里有什么

- **固定组件范围**：只使用 Vue 3、Ant Design Vue（按需在 `web/src/main.ts` 注册）和仓库内置的几个布局组件（`PageLayout`、`PageFilterBar`、`TableSection`、`CardGridSection`、`PageState`）。
- **页面范例**：`web/src/view/patterns/` 下提供了工作台、卡片列表、详情页、弹窗/抽屉与状态切换等页面，加上表格列表和设置表单，写新页面时可以直接照着结构改。
- **静态检查（`npm run check:ui`）**：检查是否引入了其他 UI/CSS 框架、模板里的 `<a-*>` 是否已在 `main.ts` 注册、业务页是否以 `PageLayout` 为根节点，以及是否存在硬编码色值或 `100vh`。
- **视口与主题检查（`npm run verify:ui`）**：无需后端，自动在桌面/窄屏和浅色/深色组合下访问页面，检查 JS 报错、请求失败和横向溢出，支持导出截图核对。

## 文档

- [AGENTS.md](AGENTS.md)：给 Coding Agent 的仓库入口和提交前检查项
- [UI / UX 设计规范](docs/ui.md)：设计原则、排版与配色、组件用法和页面参考
- [用 AI 生成一致的页面](docs/ai-page-workflow.md)：提示词示例、实现顺序和验收项
- [后端编码规范](docs/backend.md)：可选后端的分层、API 契约、SQL 与安全约定
- [文档索引](docs/README.md)：按任务查找文档

## 纯前端预览

不需要启动 PostgreSQL 或后端，在 `web/` 目录下可以直接运行范例库和检查脚本：

```bash
cd web
npm ci
npm run dev:preview                  # 启动纯前端预览（默认 http://127.0.0.1:5173）
npm run check:ui                     # 运行 UI 静态检查
npm run verify:ui                    # 检查全部范例页（桌面/窄屏 × 浅色/深色）
npm run verify:ui -- --screenshots   # 检查并保存截图到 web/.ui-verify/
```

其他常用命令：`npm run typecheck`、`npm run lint`、`npm run build`。

## 完整前后端运行（可选）

如果需要使用登录、权限管理、动态菜单和审计日志，可以启动内置的 FastAPI + PostgreSQL 服务。

### Docker Compose

1. 复制根目录的 `.env.example` 为 `.env`，填写独立的随机值 `SECRET_KEY` 和 `POSTGRES_PASSWORD`（可用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成）。
2. 运行 `docker compose up -d --build`，API 首次启动会自动初始化表结构、菜单和权限。
3. 运行 `docker compose exec api python -m app.create_admin` 设置 `admin` 密码。
4. 访问 `http://localhost:8080` 登录（端口可通过 `WEB_PORT` 修改）。

### 本地联调

环境要求：Python 3.12、Node.js 22 和一个空的 PostgreSQL 数据库。

```bash
# 后端（在 api/ 下创建虚拟环境并配置 api/.env）
python -m app.create_admin
python -m uvicorn app.main:app --host 127.0.0.1 --port 9394 --reload

# 前端（在 web/ 下）
npm run dev
```

访问 `http://127.0.0.1:5173`（Vite 会把 `/api` 代理到后端）。扩展新业务模块见 [模块开发指南](docs/module-development.md)。

## 安全性

内置的全栈底座在认证、授权、数据访问和运维配置上默认提供以下安全机制：

- **密码与会话控制**：前端登录前对密码做 SHA-256 摘要，后端使用带随机盐的 PBKDF2-SHA256（默认 260,000 次迭代）持久化；JWT 通过 `token_version` 支持即时失效（登出、改密、用户状态/角色变更或重置 2FA 时自动撤销历史令牌），并内置连续登录失败临时锁定机制。
- **可选双因素认证（2FA）**：用户可在「账户中心 → 安全设置」自主开启或关闭基于标准 TOTP（RFC 6238）的双因素认证，开启时一次性生成 8 组加盐哈希存储的恢复码用于应急登录；TOTP 密钥使用 Fernet 对称加密落库（可通过 `TOTP_ENCRYPTION_KEY` 独立配置），二阶段登录临时票据与正式访问令牌严格隔离，验证支持防重放并计入失败锁定；管理员可在用户管理中紧急重置普通用户的 2FA。
- **后端唯一授权边界与审计**：动态菜单仅控制前端导航展示，所有受保护接口由后端统一校验登录态与用户组操作权限（RBAC）；登录、登录失败、退出及关键管理写操作均记录审计日志，并附带服务端生成的 `X-Trace-Id` 便于链路排查。
- **参数化 SQL 与启动配置校验**：后端原生 SQL 全量参数化执行，避免注入风险；启动前自动检查 `SECRET_KEY` 强度、生产环境关闭 `DEBUG`、CORS Origin 合法性及 2FA 加密密钥格式，且日志、异常响应与启动报错均不泄露密码、Token 或完整密钥。更多细则见 [后端编码规范](docs/backend.md#五安全与鉴权规范)。

## 开源发布说明

本项目从 Mori 的管理后台基础模块整理而来。公开发布前，需要确认许可证、权利人信息以及第三方代码和素材声明。
