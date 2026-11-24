# UI / UX 设计规范

适用于 `web/src/view/` 下的所有页面。项目以 **Vue 3 + Ant Design Vue + 仓库公共布局组件** 构建统一的企业级后台体验，**不引入任何额外的 UI 或 CSS 框架**。

本规范参考 Ant Design 5（自然、确定）、IBM Carbon Design System 与 Refactoring UI 的企业级产品设计原则，目标不仅是「功能能跑」，更是让 AI Agent 产出的页面具备**专业设计师的克制感、秩序感与高完成度**，消除常见的「AI 生成味」与「廉价模板感」。

---

## 一、设计原则与「去 AI 味 / 去廉价感」红线

### 核心原则

1. **克制优于装饰**：后台是高频工作台而非营销落地页，信息密度、扫读效率与操作确定性永远优先于视觉炫技。
2. **主次分明，拒绝平均用力**：一个视口内只建立 1 个主视觉焦点与 1 个主操作（`type="primary"`）；主内容承担主要空间，次要信息主动退后。
3. **用结构与排版拉开层次**：优先通过字号/字重对比、留白节奏、细边框（`1px solid var(--ant-color-border-secondary)`）和浅灰阶背景建立层级，而不是靠堆叠重阴影和花哨色块。
4. **语义驱动，而非主观配色**：所有颜色、圆角、阴影与动效均来自 `--ant-*` 与 `--mori-admin-*` Token，确保浅色与深色模式同样自然耐看。
5. **面向真实边界设计**：不只设计「满屏完美数据」，必须同时考虑加载态、空态、筛选无结果、接口失败、超长文本与窄屏折行。

### 明确禁止的「AI 味 / 廉价感」反模式

生成或修改页面时，必须主动规避以下典型廉价/模板化特征：

- **禁止营销风装饰**：禁止在后台业务页加入紫蓝渐变 Hero Banner、霓虹发光阴影（glow）、滥用毛玻璃（`backdrop-filter`），或带 Emoji 的客套标题（如 `🚀 欢迎回来，管理员！`、`✨ 智能概览`）。
- **禁止无意义的图标徽章**：禁止给每个 KPI 卡片或区块标题强行配一个「彩色圆角底块 + 图标」的装饰徽章；只有图标能显著加速类别识别时才使用。
- **禁止卡片套卡片（多层嵌套）**：容器嵌套不超过 2 层，禁止「外层大卡片 → 内层小卡片 → 更小圆角块」的俄罗斯套娃式边框；内部分区改用留白、`a-divider` 或 `--ant-color-fill-quaternary` 弱底色块。
- **禁止彩虹标签墙与伪指标**：禁止给每个普通字段都套五颜六色的 `a-tag`；禁止为了填满页面而强行拼凑 4 张权重完全相同、配着虚构 `+12.5%` 绿标的同质化 KPI 卡片。
- **禁止视觉过载**：禁止一屏出现多个实心 `type="primary"` 主按钮；禁止超大圆角（`20px+`）与发脏的深重投影。

---

## 二、视觉基础规范

### 1. 排版与数字（Typography）

基于 Ant Design Vue `14px` 基准字号，严格保持清晰字阶，避免随意出现 `15px`、`17px`、`22px` 等零散字号：

| 层级 | 字号 / 字重 / 行高 | 颜色 Token | 适用场景 |
| --- | --- | --- | --- |
| 页面标题 | `20px` / `600` / `1.4` | `--ant-color-text` | 由 `PageToolbar` 统一提供，业务页不重复手写 `h1`/`h2` |
| 区块 / 卡片标题 | `16px` / `600` / `1.4` | `--ant-color-text` | `a-card` 标题、表单分组标题 |
| 正文 / 表单 / 表格 | `14px` / `400` / `1.5` | `--ant-color-text` | 列表正文、表单项、正文说明 |
| 次要信息 / 表头辅助 | `12px–13px` / `400` / `1.5` | `--ant-color-text-secondary` | 页面副标题、指标标签、次要描述 |
| 弱提示 / 时间戳 | `12px` / `400` / `1.5` | `--ant-color-text-tertiary` | 更新时间、底部注释、次要元信息 |
| 关键指标数值 | `24px–28px` / `600` / `1.25` | `--ant-color-text` | 工作台核心数值（必须配合等宽数字） |

- **等宽数字对齐**：所有指标卡片数值、表格数字列、金额、耗时、百分比必须设置 `font-variant-numeric: tabular-nums;`，保证纵向对齐且数值变化时不抖动。
- **文本截断与换行**：用户名、邮箱、长标题、URL 必须显式处理溢出（单行 `text-overflow: ellipsis` + `a-tooltip`，或多行 `overflow-wrap: anywhere`），禁止撑破栅格。

### 2. 色彩克制与深浅色层次（Color & Surface）

- **90 / 8 / 2 配色比例**：约 90% 为中性背景与文字，约 8% 为弱填充与细边框，仅约 2% 为品牌主色与状态语义色。
- **语义色专款专用**：
  - `primary`：仅用于主按钮、当前激活导航/标签、可点击主链接。
  - `success` / `warning` / `error`：仅用于真实的成功、告警、错误或危险状态，禁止作为装饰色轮流涂抹普通卡片或非状态标签。
- **浅色与深色层级一致**：页面表面遵循 `bg-layout`（底布）→ `bg-container`（主工作面/卡片）→ `bg-elevated`（浮层/下拉/弹窗）三层关系，辅以 `1px solid var(--ant-color-border-secondary)` 细边框清晰界定边界，不靠浓黑阴影在深色模式下「抹黑」界面。

### 3. 间距、亲密性与阅读宽度（Spacing & Layout）

- **4px / 8px 空间网格**：
  - 元素内紧间距：`4px` / `8px`（如图标与文字、标签与控件）。
  - 同组关联间距：`12px`（如快捷入口列表项之间、工具栏控件组）。
  - 区块与卡片间距：`var(--mori-admin-section-gap)`（`16px`）。
  - 独立大分区间距：`24px`（如长表单的大节分隔）。
  - 页面外边距统一由 `PageLayout` 接管（桌面 `24px`，窄屏 `12px`），业务页禁止再套一层页面级 padding。
- **亲密性原则**：同一信息单元内部间距必须明显小于不同单元之间的间距，无需到处加分割线即可一眼看出归属。
- **受控阅读宽度**：设置表单、个人资料、详情页必须通过 `PageLayout` 的 `max-width`（通常 `720px`–`1040px`）收敛宽度，避免在 1440px 以上宽屏被拉成难以扫读的扁平长条。

### 4. 动效与微交互（Motion）

统一消费 [theme.scss](../web/src/styles/theme.scss) 的动效 Token 与 [transition.scss](../web/src/styles/transition.scss) 的过渡类：

- `--mori-admin-motion-fast`（`140ms`）：按钮 hover、标签态变、焦点反馈、局部状态切换（`fade-scale`）。
- `--mori-admin-motion-base`（`200ms`）：路由页面切换（`fade-transform`）、高级筛选展开收起、深浅色背景切换（`fade`）。
- `--mori-admin-motion-slow`（`260ms`）：侧边栏展开/收起、移动端抽屉滑入滑出。
- 缓动曲线使用 `--mori-admin-ease-standard` / `ease-out` / `ease-in`，仅对 `opacity`、`transform`、`color`、`background-color`、`border-color` 等轻量属性做过渡，并尊重系统的 `prefers-reduced-motion: reduce`。

---

## 三、高频场景交互与文案细则

### 1. 数据表格（`TableSection` + `a-table`）

- **列对齐规范**：文本类左对齐；数字/金额/数量/耗时右对齐（配 `tabular-nums`）；短状态徽标与操作列保持统一对齐。
- **字段优先级**：主识别字段（名称/账号/标题）放首列，核心状态紧随其后，次要 ID 与时间戳靠后；长文本列设置 `ellipsis: true`。
- **行内操作收敛**：每行直接展示的高频动作不超过 2–3 个（如「编辑」「详情」），超出部分收进 `a-dropdown`「更多」菜单；危险动作使用 `a-popconfirm`。

### 2. 表单与数据录入（`a-form`）

- **标签布局**：优先使用顶置标签（`layout="vertical"`），垂直扫读效率高且窄屏天然兼容；仅在极短且强关联的字段（如起止时间、省市）时使用双列并排。
- **分组与校验**：超过 6 个字段时按业务主题分组；优先在失焦或输入时给出清晰的字段级校验提示；提交按钮绑定 `:loading` 防止重复提交。

### 3. 按钮层级与交互容器边界

- **主操作唯一**：每个页面工具栏、弹窗、抽屉内最多 1 个 `type="primary"` 实心主按钮；次要操作使用默认按钮，低频操作收进 `PageToolbarMore`，行内操作使用 `type="link"` 或 `type="text"`。
- **Modal（`a-modal`）**：字段 ≤ 5 项、单步聚焦决策的轻量新建、重命名或确认操作。
- **Drawer（`a-drawer`）**：字段较多、需要分节说明或需要对照原列表查看/编辑时使用，宽度使用 `min(520px, 100vw)` 等自适应写法。
- **Popconfirm（`a-popconfirm`）**：删除、停用、重置等不可逆危险操作，提供明确后果说明与 `ok-type="danger"`。

### 4. 专业微文案与完整状态（Microcopy & States）

- **动宾明确的按钮文案**：用「新建角色」「保存配置」「导出日志」替代模糊的「确定」「提交」「点击这里」。
- **可执行的错误反馈**：写清「发生了什么 + 如何处理」（如「保存失败：该邮箱已被占用，请更换后重试」），禁止只弹「操作失败」「系统异常」。
- **有引导的空状态**：使用 `PageState` 区分「初次无数据（说明用途并提供新建主按钮）」与「筛选无匹配结果（提供一键重置筛选按钮）」。
- **保留现场**：已有列表数据时局部刷新失败，使用 `a-alert` 提示并保留旧数据，不清空页面。

---

## 四、按页面类型选参考

实现新页面前，先从下表选一个最接近的真实页面作为结构锚点，再填入业务内容：

| 页面类型 | 参考实现 | 布局选择 |
| --- | --- | --- |
| 工作台 / 数据概览 | [工作台概览](../web/src/view/patterns/workspace.vue) | `PageLayout` 页面滚动，指标卡片使用响应式 CSS Grid，主次双栏卡片在窄屏自动折行。 |
| 卡片网格列表 | [卡片网格列表](../web/src/view/patterns/cardGrid.vue) | `PageLayout scroll="region"`、`PageFilterBar`（含高级筛选）、`CardGridSection`、`PageState`。 |
| 详情与分区展示 | [详情与分区页](../web/src/view/patterns/detail.vue) | `PageLayout` 页面滚动 + `max-width`，工具栏含 `PageToolbarMore`，内容用 `a-descriptions` + `a-tabs`。 |
| 弹窗、抽屉与状态反馈 | [弹窗抽屉与状态](../web/src/view/patterns/drawerForm.vue) | 演示 `a-modal` vs `a-drawer` 选用边界、`a-popconfirm` 与 `PageState` 三态切换。 |
| 有筛选和分页的表格 | [登录日志](../web/src/view/security-audit/loginLog.vue) | `PageLayout scroll="region"`、`PageFilterBar`、`TableSection`。 |
| 带新增、编辑或删除的管理列表 | [用户管理](../web/src/view/system/user.vue) | 沿用表格列表布局，主操作放工具栏，单条记录动作放行内。 |
| 资料或设置表单 | [个人资料](../web/src/view/account/profile.vue)、[品牌设置](../web/src/view/system/branding.vue) | `PageLayout` 页面滚动，内容用单个 `a-card` 分组。 |

[登录页](../web/src/view/login/index.vue)和 [404 页](../web/src/view/404/index.vue)是独立入口。所有其他业务页均沿用外壳并以 `PageLayout` 为根节点。

---

## 五、公共组件怎么用

| 组件 | 用法 |
| --- | --- |
| [PageLayout](../web/src/components/PageLayout/index.vue) | 页面外层。标准布局提供 `#actions` 和 `#filter`，主内容放默认插槽。详情/表单/工作台用 `scroll="page"`，表格/卡片列表用 `scroll="region"`。 |
| [PageFilterBar](../web/src/components/PageFilterBar/index.vue) | 基础字段放 `#basic`，查询和重置放 `#submit`，折叠项按需放 `#advanced`（配合 `advanced` 属性）。 |
| [TableSection](../web/src/components/TableSection/index.vue) | 表格放默认插槽，分页放 `#footer`。表体纵向滚动，宽表格在表格区域内横向滚动。 |
| [CardGridSection](../web/src/components/CardGridSection/index.vue) | 卡片列表需要区域滚动和固定底部分页时复用；分页放 `#footer`。 |
| [PageState](../web/src/components/PageState/index.vue) | 页面级加载（`loading`）、空状态（`empty`）或失败（`error`）。局部请求失败（如已有列表数据时刷新失败）可用 `a-alert` 提示并保留旧数据。 |
| [PageRefreshButton](../web/src/components/PageRefreshButton/index.vue)、[PageToolbarMore](../web/src/components/PageToolbarMore/index.vue) | 刷新和低频页面操作按需放入 `#actions`。 |

---

## 六、硬性约束（由 `npm run check:ui` 自动门禁）

- **不引入额外 UI 框架**：禁止安装或引用 Tailwind、Element Plus、Naive UI、Bootstrap、Lucide 等额外 UI/CSS/图标库，只用已集成的 Ant Design Vue、`@ant-design/icons-vue` 与仓库公共组件。
- **组件必须已注册**：模板中使用的 `<a-*>` 标签必须已在 [main.ts](../web/src/main.ts) 注册；确实需要 Ant Design Vue 中尚未注册的组件时，先在 `main.ts` 显式按需注册。
- **布局与滚动**：业务页根节点必须为 `<PageLayout>`，禁止手写 `100vh` / `100dvh` 或在外层重复套滚动容器。
- **颜色与主题**：禁止硬编码 `#hex`、`rgb()`、`hsl()`、`white`、`black`，统一使用 `--ant-*` 主题 Token 或 [theme.scss](../web/src/styles/theme.scss) 中的 `--mori-admin-*` Token。主题由 [主题配置](../web/src/theme/config.ts) 和 [Token 上下文](../web/src/theme/ThemeContext.vue) 统一下发。
- **表单与可访问性**：沿用 `a-form` 与 `a-form-item`，绑定 `:model` 并在 `@finish` 提交；保存时显示加载防重复点击；纯图标按钮提供 Tooltip 与 `aria-label`。
