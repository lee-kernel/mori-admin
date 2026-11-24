import type { Component } from 'vue'
import Layout from '@/layout/index.vue'

type ComponentLoader = () => Promise<{ default: Component }>

/**
 * 通过 Vite 的 import.meta.glob 在编译期收集 src/view 下所有 .vue 组件。
 * key 形如 "view/system/user.vue"，对应后端菜单表的 component 字段。
 */
const rawModules = import.meta.glob('@/view/**/*.vue')

const viewModules: Record<string, ComponentLoader> = {}
for (const fullPath in rawModules) {
  const loader = rawModules[fullPath] as ComponentLoader
  // 统一去掉路径前缀，得到 "view/xxx/xxx.vue" 形式的归一化 key
  const normalizedKey = fullPath
    .replace(/^\/src\//, '')
    .replace(/^\.\.\//, '')
    .replace(/^@\//, '')
    .replace(/^src\//, '')

  viewModules[normalizedKey] = loader
}

/** 全局布局组件的固定标识；后端 component 字段填 "Layout" 即可。 */
export const LAYOUT_COMPONENT_KEY = 'Layout'

/**
 * 根据后端下发的 component 字符串解析为真正的 Vue 组件。
 * - "Layout"        → 同步引入的全局布局组件
 * - "view/xxx.vue"  → 懒加载视图组件
 * - 其他/找不到     → 返回 null，由调用方决定是否丢弃该路由
 */
export function resolveComponent(
  component: string | null | undefined
): Component | ComponentLoader | null {
  if (!component) return null
  if (component === LAYOUT_COMPONENT_KEY) return Layout
  return viewModules[component] || null
}

/**
 * 返回所有可选的 component 键（含 "Layout" 与扫描到的视图）。
 * 主要用于「菜单管理」表单里的 component 下拉选择。
 */
export function listAvailableComponents(): string[] {
  return [LAYOUT_COMPONENT_KEY, ...Object.keys(viewModules).sort()]
}
