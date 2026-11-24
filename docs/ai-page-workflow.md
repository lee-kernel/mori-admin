# 用 AI 生成一致的页面

适用于新增业务页面、改版现有页面或为页面补齐交互。核心思路是：**用范例锚定结构 + 用静态门禁防跑偏 + 用多视口视觉自检兜底**。

## 给 AI 的输入

- **页面用途**：说明谁在用、主要任务是什么、默认展示哪些信息。
- **数据和操作**：给出已有 API、字段、查询参数、允许的操作和对应权限；纯前端原型阶段可直接说明使用本地 Mock 数据。
- **参考页面**：从 [UI 规范](ui.md) 选择一种页面类型并指定仓库里的真实例子（如 `web/src/view/patterns/cardGrid.vue`）。
- **验收场景**：列出正常流程和重要边界，比如空结果、失败重试、翻页、窄屏或暗色模式。

## 实现顺序

1. 读 [AGENTS.md](../AGENTS.md)、[UI 规范](ui.md) 和最接近的参考页面源码，核对 `PageLayout`、`main.ts` 已注册组件与公共组件用法。
2. 先搭页面骨架：确定标题、主操作、筛选、内容与分页位置，选定 `scroll="page"` 或 `scroll="region"`。
3. 接入真实接口或本地 Mock 数据；条件未明确时说明缺口，不虚构接口字段或权限。
4. 运行自动化门禁与自检：
   - 在 `web/` 运行 `npm run typecheck`、`npm run check:ui` 与 `npm run lint`；
   - 运行 `npm run verify:ui -- /你的路由`（可加 `--screenshots`），自动验证桌面/窄屏 × 浅色/深色下无报错、无横向溢出；
   - 涉及路由、构建或公共组件时再运行 `npm run build`。

## 可复制的任务提示词

```text
实现「资源模板」卡片列表页。先读 AGENTS.md、docs/ai-page-workflow.md 和 docs/ui.md。
严格遵循只使用现有 Ant Design Vue 与仓库公共组件的原则，不引入额外 UI/CSS 框架；
遵循 docs/ui.md 中的克制配色、排版数字对齐与去「AI 味」规范（不堆砌装饰图标、不卡片套卡片、仅保留一个主操作按钮）。
以 web/src/view/patterns/cardGrid.vue 为参考，复用 PageLayout(scroll="region")、
PageFilterBar、CardGridSection 和 PageState。
支持关键词搜索、分类筛选、分页，并处理加载中、空数据和请求失败重试。
完成后运行 npm run typecheck、npm run check:ui、npm run lint 和 npm run verify:ui 验证并汇报结果。
```

## 验收项

| 检查项 | 通过条件 | 验证方式 |
| --- | --- | --- |
| 框架纯净 | 未引入额外 UI/CSS 框架，`<a-*>` 均已在 `main.ts` 注册 | `npm run check:ui` |
| 布局与主题 | 根节点为 `PageLayout`，无硬编码色值、无 `100vh` | `npm run check:ui` |
| 设计质感与克制 | 主次清晰、无卡片多层嵌套/装饰性渐变/彩虹标签墙，数字对齐、按钮文案动宾明确 | 对照 `docs/ui.md` 审阅 |
| 类型与代码风格 | TS 与 Vue 模板无类型错误，符合 ESLint 与 Prettier | `npm run typecheck`、`npm run lint` |
| 状态与交互 | 加载、无数据和失败有可区分反馈，提交防重复点击，危险操作有确认 | 代码审阅 / 交互验证 |
| 视觉与适配 | 浅色/深色、桌面/窄屏下无 JS 报错、无横向溢出、主操作可见 | `npm run verify:ui`（可附 `--screenshots`） |
