#!/usr/bin/env node
/**
 * UI 静态门禁检查（零外部依赖，供人类与 AI Agent 在提交前运行）。
 *
 * 检查项：
 * 1. 禁止引入额外的 UI 组件库、CSS 框架或图标库（坚持只使用 Vue 3 + Ant Design Vue + 仓库公共组件）。
 * 2. 校验模板中使用的 <a-*> 标签均已在 src/main.ts 注册，避免运行时静默失效。
 * 3. 业务页面（src/view/**，不含登录页和 404 页）根节点必须为 <PageLayout>。
 * 4. 业务页面禁止硬编码颜色（#hex / rgb / hsl / white / black），强制使用 --ant-* 或 --mori-admin-* Token。
 * 5. 业务页面禁止手写视口高度单位（vh / dvh / svh / lvh），滚动与高度由 PageLayout 统一接管。
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const WEB_ROOT = path.resolve(__dirname, '..')
const SRC_ROOT = path.join(WEB_ROOT, 'src')
const VIEW_ROOT = path.join(SRC_ROOT, 'view')
const MAIN_TS_PATH = path.join(SRC_ROOT, 'main.ts')
const PKG_JSON_PATH = path.join(WEB_ROOT, 'package.json')

/** 独立入口页面（不套后台外壳，跳过 PageLayout 根节点、颜色与 vh 限制）。 */
const STANDALONE_VIEWS = new Set(['view/login/index.vue', 'view/404/index.vue'])

/** 禁止引入的额外 UI 组件库、CSS 框架与图标库。 */
const FORBIDDEN_UI_PACKAGES = [
  'element-plus',
  'element-ui',
  'naive-ui',
  'vuetify',
  'primevue',
  '@arco-design/web-vue',
  'tdesign-vue-next',
  'vant',
  'quasar',
  '@headlessui/vue',
  'radix-vue',
  'reka-ui',
  'shadcn-vue',
  'view-ui-plus',
  'varlet',
  'tailwindcss',
  '@tailwindcss/vite',
  '@tailwindcss/postcss',
  'unocss',
  'windicss',
  'bootstrap',
  'bulma',
  'daisyui',
  'lucide-vue-next',
  '@heroicons/vue',
  '@element-plus/icons-vue',
]

/**
 * Ant Design Vue 按模块注册时附带注册的子组件标签映射。
 * key 为 `ant-design-vue/es/<module>` 的模块名。
 */
const ANTD_SUBCOMPONENTS = {
  alert: ['a-alert'],
  app: ['a-app'],
  'auto-complete': ['a-auto-complete', 'a-auto-complete-option', 'a-auto-complete-opt-group'],
  avatar: ['a-avatar', 'a-avatar-group'],
  badge: ['a-badge', 'a-badge-ribbon'],
  breadcrumb: ['a-breadcrumb', 'a-breadcrumb-item', 'a-breadcrumb-separator'],
  button: ['a-button', 'a-button-group'],
  card: ['a-card', 'a-card-grid', 'a-card-meta'],
  cascader: ['a-cascader'],
  checkbox: ['a-checkbox', 'a-checkbox-group'],
  collapse: ['a-collapse', 'a-collapse-panel'],
  'config-provider': ['a-config-provider'],
  'date-picker': [
    'a-date-picker',
    'a-month-picker',
    'a-week-picker',
    'a-range-picker',
    'a-quarter-picker',
  ],
  descriptions: ['a-descriptions', 'a-descriptions-item'],
  divider: ['a-divider'],
  drawer: ['a-drawer'],
  dropdown: ['a-dropdown', 'a-dropdown-button'],
  empty: ['a-empty'],
  flex: ['a-flex'],
  form: ['a-form', 'a-form-item', 'a-form-item-rest'],
  grid: ['a-row', 'a-col'],
  image: ['a-image', 'a-image-preview-group'],
  input: ['a-input', 'a-input-group', 'a-input-password', 'a-input-search', 'a-textarea'],
  'input-number': ['a-input-number'],
  layout: ['a-layout', 'a-layout-header', 'a-layout-footer', 'a-layout-content', 'a-layout-sider'],
  list: ['a-list', 'a-list-item', 'a-list-item-meta'],
  menu: ['a-menu', 'a-menu-item', 'a-menu-item-group', 'a-menu-divider', 'a-sub-menu'],
  modal: ['a-modal'],
  pagination: ['a-pagination'],
  popconfirm: ['a-popconfirm'],
  popover: ['a-popover'],
  progress: ['a-progress'],
  radio: ['a-radio', 'a-radio-group', 'a-radio-button'],
  result: ['a-result'],
  segmented: ['a-segmented'],
  select: ['a-select', 'a-select-option', 'a-select-opt-group'],
  skeleton: [
    'a-skeleton',
    'a-skeleton-avatar',
    'a-skeleton-button',
    'a-skeleton-image',
    'a-skeleton-input',
    'a-skeleton-title',
  ],
  space: ['a-space', 'a-space-compact'],
  spin: ['a-spin'],
  statistic: ['a-statistic', 'a-statistic-countdown'],
  steps: ['a-steps', 'a-step'],
  switch: ['a-switch'],
  table: [
    'a-table',
    'a-table-column',
    'a-table-column-group',
    'a-table-summary',
    'a-table-summary-row',
    'a-table-summary-cell',
  ],
  tabs: ['a-tabs', 'a-tab-pane'],
  tag: ['a-tag', 'a-checkable-tag'],
  'time-picker': ['a-time-picker', 'a-time-range-picker'],
  timeline: ['a-timeline', 'a-timeline-item'],
  tooltip: ['a-tooltip'],
  tree: ['a-tree', 'a-directory-tree'],
  'tree-select': ['a-tree-select', 'a-tree-select-node'],
  typography: [
    'a-typography',
    'a-typography-title',
    'a-typography-paragraph',
    'a-typography-text',
    'a-typography-link',
  ],
  upload: ['a-upload', 'a-upload-dragger'],
}

/** @type {Array<{ file: string, line?: number, rule: string, message: string }>} */
const violations = []

function report(file, rule, message, line) {
  violations.push({
    file: path.relative(WEB_ROOT, file).replace(/\\/g, '/'),
    line,
    rule,
    message,
  })
}

function walkFiles(dir, extensions) {
  if (!fs.existsSync(dir)) return []
  const result = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      result.push(...walkFiles(full, extensions))
    } else if (extensions.some((ext) => entry.name.endsWith(ext))) {
      result.push(full)
    }
  }
  return result
}

function lineNumberAt(content, index) {
  return content.slice(0, index).split(/\r?\n/).length
}

function extractBlock(content, tagName) {
  const regex = new RegExp(`<${tagName}\\b[^>]*>([\\s\\S]*?)<\\/${tagName}>`, 'gi')
  const blocks = []
  let match
  while ((match = regex.exec(content)) !== null) {
    const startOffset = match.index + match[0].indexOf('>') + 1
    blocks.push({ content: match[1], offset: startOffset })
  }
  return blocks
}

function extractTopLevelTemplate(content) {
  const openMatch = /<template\b[^>]*>/i.exec(content)
  if (!openMatch) return null
  const start = openMatch.index + openMatch[0].length
  const closeIndex = content.lastIndexOf('</template>')
  if (closeIndex <= start) return null
  return { content: content.slice(start, closeIndex), offset: start }
}

function checkForbiddenPackages() {
  const pkg = JSON.parse(fs.readFileSync(PKG_JSON_PATH, 'utf8'))
  const allDeps = { ...pkg.dependencies, ...pkg.devDependencies }
  for (const forbidden of FORBIDDEN_UI_PACKAGES) {
    if (Object.prototype.hasOwnProperty.call(allDeps, forbidden)) {
      report(
        PKG_JSON_PATH,
        'no-extra-ui-framework',
        `禁止引入额外 UI/CSS 框架 "${forbidden}"；请使用项目既有的 Ant Design Vue 与公共组件。`
      )
    }
  }

  const sourceFiles = walkFiles(SRC_ROOT, ['.vue', '.ts', '.tsx', '.js', '.scss', '.css'])
  for (const file of sourceFiles) {
    const content = fs.readFileSync(file, 'utf8')
    for (const forbidden of FORBIDDEN_UI_PACKAGES) {
      const escaped = forbidden.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const importRegex = new RegExp(
        `(?:from|import|@use|@import)\\s+['"]${escaped}(?:\\/[^'"]*)?['"]`,
        'g'
      )
      const match = importRegex.exec(content)
      if (match) {
        report(
          file,
          'no-extra-ui-framework',
          `禁止引用额外 UI/CSS 框架 "${forbidden}"；请复用项目既有的 Ant Design Vue 与公共组件。`,
          lineNumberAt(content, match.index)
        )
      }
    }
  }
}

function collectRegisteredAntdTags() {
  const mainContent = fs.readFileSync(MAIN_TS_PATH, 'utf8')
  const importRegex = /import\s+\w+\s+from\s+['"]ant-design-vue\/es\/([a-z0-9-]+)['"]/g
  const allowedTags = new Set()
  let match
  while ((match = importRegex.exec(mainContent)) !== null) {
    const mod = match[1]
    const tags = ANTD_SUBCOMPONENTS[mod] || [`a-${mod}`]
    for (const tag of tags) {
      allowedTags.add(tag)
    }
  }
  return allowedTags
}

function checkRegisteredAntdComponents(allowedTags) {
  const vueFiles = walkFiles(SRC_ROOT, ['.vue'])
  for (const file of vueFiles) {
    const content = fs.readFileSync(file, 'utf8')
    const tpl = extractTopLevelTemplate(content)
    if (!tpl) continue

    // 移除 HTML 注释，保留换行长度以维持行号准确
    const cleaned = tpl.content.replace(/<!--[\s\S]*?-->/g, (m) => m.replace(/[^\r\n]/g, ' '))
    const tagRegex = /<(a-[a-z][a-z0-9-]*)(?=[\s/>])/g
    const reportedInFile = new Set()
    let match
    while ((match = tagRegex.exec(cleaned)) !== null) {
      const tagName = match[1]
      if (!allowedTags.has(tagName) && !reportedInFile.has(tagName)) {
        reportedInFile.add(tagName)
        report(
          file,
          'registered-antd-component',
          `模板使用了未在 src/main.ts 注册的组件 <${tagName}>；请改用已注册组件，或在确认必要后先于 src/main.ts 注册。`,
          lineNumberAt(content, tpl.offset + match.index)
        )
      }
    }
  }
}

function checkViews() {
  const viewFiles = walkFiles(VIEW_ROOT, ['.vue'])
  for (const file of viewFiles) {
    const relFromSrc = path.relative(SRC_ROOT, file).replace(/\\/g, '/')
    if (STANDALONE_VIEWS.has(relFromSrc)) continue

    const content = fs.readFileSync(file, 'utf8')
    const tpl = extractTopLevelTemplate(content)
    if (!tpl) continue

    // 1. 根节点必须是 <PageLayout>
    const strippedTpl = tpl.content.replace(/<!--[\s\S]*?-->/g, '').trimStart()
    if (!/^<PageLayout\b/.test(strippedTpl)) {
      report(
        file,
        'require-page-layout',
        '业务页面根节点必须使用 <PageLayout>；独立入口页请单独登记。',
        lineNumberAt(content, tpl.offset)
      )
    }

    // 2. 模板内联 style 检查（禁止硬编码颜色和 vh）
    const inlineStyleRegex = /\bstyle\s*=\s*"([^"]*)"/gi
    let styleMatch
    while ((styleMatch = inlineStyleRegex.exec(tpl.content)) !== null) {
      const val = styleMatch[1]
      const line = lineNumberAt(content, tpl.offset + styleMatch.index)
      if (/(#[0-9a-f]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\()/i.test(val)) {
        report(
          file,
          'no-hardcoded-color',
          '禁止在模板内联 style 中硬编码颜色值，请使用 --ant-* 或 --mori-admin-* 主题 Token。',
          line
        )
      }
      if (/\b100[dsl]?vh\b/i.test(val)) {
        report(
          file,
          'no-viewport-height',
          '禁止在业务页面中手写 100vh/100dvh 高度，请使用 PageLayout 的 scroll="page" 或 scroll="region"。',
          line
        )
      }
    }

    // 3. <style> 块检查（禁止硬编码颜色和 100vh）
    const styleBlocks = extractBlock(content, 'style')
    for (const block of styleBlocks) {
      // 移除 CSS/SCSS 注释但保留换行
      const cleaned = block.content
        .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\r\n]/g, ' '))
        .replace(/\/\/[^\r\n]*/g, (m) => ' '.repeat(m.length))

      const colorRegex =
        /(#[0-9a-f]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\(|:\s*(?:white|black)\s*[;!])/gi
      let match
      while ((match = colorRegex.exec(cleaned)) !== null) {
        report(
          file,
          'no-hardcoded-color',
          `禁止硬编码颜色 "${match[0].trim()}"，请改用 --ant-* 或 --mori-admin-* 主题 Token 以保证浅色/深色一致。`,
          lineNumberAt(content, block.offset + match.index)
        )
      }

      const vhRegex = /\b100[dsl]?vh\b/gi
      while ((match = vhRegex.exec(cleaned)) !== null) {
        report(
          file,
          'no-viewport-height',
          `禁止在业务页样式中使用 "${match[0]}"，请交由 PageLayout 统一管理高度与滚动。`,
          lineNumberAt(content, block.offset + match.index)
        )
      }
    }
  }
}

function main() {
  checkForbiddenPackages()
  const allowedTags = collectRegisteredAntdTags()
  checkRegisteredAntdComponents(allowedTags)
  checkViews()

  if (violations.length > 0) {
    console.error(`\n[check:ui] 发现 ${violations.length} 项 UI 规范违规：\n`)
    for (const v of violations) {
      const loc = v.line ? `${v.file}:${v.line}` : v.file
      console.error(`  ✗ [${v.rule}] ${loc}`)
      console.error(`    ${v.message}`)
    }
    console.error('')
    process.exit(1)
  }

  console.log('[check:ui] 所有 UI 规范门禁检查通过。')
}

main()
