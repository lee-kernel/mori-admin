# Mori 文档索引

Mori 分为两层：**面向 AI Agent 的 UI 约束框架（核心层）** 与 **可选的 FastAPI + PostgreSQL 全栈后台底座**。按任务读取对应指南，然后打开最接近的参考页面源码。

| 任务 | 从这里开始 |
| --- | --- |
| 给仓库内的 Coding Agent 设定入口与门禁 | [AGENTS.md](../AGENTS.md) |
| 用 AI 新建或修改页面（含提示词与自检） | [页面生成流程和提示词示例](ai-page-workflow.md) |
| 选择布局原语、视觉与交互规范、反模式红线与范例页 | [UI / UX 设计规范](ui.md) |
| 纯前端预览范例库 & 运行 UI 自动化检查 | [项目 README](../README.md#纯前端预览) |
| 修改后端 API、SQL、迁移或安全边界 | [后端编码规范](backend.md)、[api/AGENTS.md](../api/AGENTS.md) |
| 接入可选全栈底座（新增完整业务模块） | [模块开发指南](module-development.md) |

参考页面随项目运行；纯前端模式执行 `npm --prefix web run dev:preview` 即可直接查看全部标准范例页。
