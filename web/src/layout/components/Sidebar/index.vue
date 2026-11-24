<template>
  <div class="sidebar-shell" :class="{ 'has-logo': showLogo }">
    <Logo :collapse="isCollapse" :show-logo="showLogo" />

    <div class="sidebar-scrollbar scrollbar-wrapper">
      <a-menu
        v-model:open-keys="openKeys"
        v-model:selected-keys="selectedKeys"
        :items="menuItems"
        :inline-collapsed="isCollapse"
        mode="inline"
        @click="handleMenuClick" />
    </div>

    <SidebarAccount :collapse="isCollapse" />
  </div>
</template>

<script lang="ts" setup>
import { computed, h, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { MenuInfo } from 'ant-design-vue/es/menu/src/interface'
import type { MenuProps } from 'ant-design-vue'
import * as AntIcons from '@ant-design/icons-vue'
import { isExternal } from '@/utils/validate'
import { useAppStore } from '@/stores/app'
import { useSettingsStore } from '@/stores/setting'
import { useUserStore } from '@/stores/user'
import type { MenuNode } from '@/api/menu'
import Logo from './Logo.vue'
import SidebarAccount from './SidebarAccount.vue'

type MenuItem = NonNullable<MenuProps['items']>[number]

const SIDEBAR_OPEN_KEYS_KEY = 'mori_admin_sidebar_open_keys'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const settingsStore = useSettingsStore()
const userStore = useUserStore()

const showLogo = computed(() => settingsStore.sidebarLogo)
const isCollapse = computed(() => !appStore.sidebar.opened)
/**
 * 编译后的菜单数据。同时返回：
 * - items：a-menu 所需 items 配置
 * - submenuKeys：所有 SubMenu 的 key（用于过滤 localStorage 中已失效的展开记录）
 * - pathToKey：业务 path → 菜单 key 的映射（用于将路由 path 映射回菜单选中态）
 */
const compiledMenu = computed(() => compileMenu(userStore.menus))
const menuItems = computed(() => compiledMenu.value.items)

// antd Menu 通过 v-model 自己维护，组件内不再做合并/拦截
const openKeys = ref<string[]>(restoreOpenKeys())
const selectedKeys = ref<string[]>([resolveActiveKey()])

// 持久化展开项（普通 watch 即可，无需 deep）
watch(openKeys, (keys) => localStorage.setItem(SIDEBAR_OPEN_KEYS_KEY, JSON.stringify(keys)))

// 路由变化：同步选中态，并确保所有祖先 SubMenu 处于展开状态
watch(
  () => route.path,
  () => {
    selectedKeys.value = [resolveActiveKey()]
    if (isCollapse.value) return

    const ancestors = ancestorKeysOf(selectedKeys.value[0])
    const missing = ancestors.filter((k) => !openKeys.value.includes(k))
    if (missing.length) {
      openKeys.value = [...openKeys.value, ...missing]
    }
  },
  { immediate: true }
)

// 菜单结构发生变化（如切换账号、权限刷新）时，清掉已不存在的展开 key
watch(
  () => compiledMenu.value.submenuKeys,
  (validKeys) => {
    const valid = new Set(validKeys)
    const filtered = openKeys.value.filter((k) => valid.has(k))
    if (filtered.length !== openKeys.value.length) {
      openKeys.value = filtered
    }
  }
)

/** 当前路由对应的菜单 key（优先取 route.meta.activeMenu） */
function resolveActiveKey(): string {
  const explicit = route.meta.activeMenu as string | undefined
  const path = explicit || route.path
  // 单子节点折叠的菜单，path 不一定直接命中菜单 key，借助映射做兜底
  return compiledMenu.value.pathToKey.get(path) || path
}

/**
 * 找到 selectedKey 对应的菜单节点，向上回溯收集所有祖先 SubMenu 的 key。
 * 相比"只取一级父路径"，可正确支持多级菜单的自动展开。
 */
function ancestorKeysOf(selectedKey: string): string[] {
  const parents = compiledMenu.value.parentMap
  const result: string[] = []
  let cur = parents.get(selectedKey)
  while (cur) {
    result.push(cur)
    cur = parents.get(cur)
  }
  return result
}

interface CompiledMenu {
  items: MenuItem[]
  submenuKeys: string[]
  pathToKey: Map<string, string>
  parentMap: Map<string, string> // childKey → parentKey
}

/** 把后端菜单树编译为 a-menu items，并同时收集映射信息 */
function compileMenu(nodes: MenuNode[]): CompiledMenu {
  const submenuKeys: string[] = []
  const pathToKey = new Map<string, string>()
  const parentMap = new Map<string, string>()

  function build(node: MenuNode, parentKey: string | null): MenuItem | null {
    if (node.hidden) return null
    const visibleChildren = (node.children || []).filter((c) => !c.hidden)

    // 仅一个可见子节点且子节点无更深层级 → 直接展示子节点，不再额外嵌套
    if (visibleChildren.length === 1 && !(visibleChildren[0].children || []).length) {
      const child = visibleChildren[0]
      pathToKey.set(child.path, child.path)
      pathToKey.set(node.path, child.path)
      if (parentKey) parentMap.set(child.path, parentKey)
      return {
        key: child.path,
        icon: renderIcon(node.icon || child.icon),
        label: child.name,
      }
    }

    // 叶子节点
    if (!visibleChildren.length) {
      pathToKey.set(node.path, node.path)
      if (parentKey) parentMap.set(node.path, parentKey)
      return {
        key: node.path,
        icon: renderIcon(node.icon),
        label: node.name,
      }
    }

    // 分组节点（SubMenu）
    const children = visibleChildren.map((c) => build(c, node.path)).filter(Boolean) as MenuItem[]
    if (!children.length) return null

    submenuKeys.push(node.path)
    pathToKey.set(node.path, node.path)
    if (parentKey) parentMap.set(node.path, parentKey)

    return {
      key: node.path,
      icon: renderIcon(node.icon),
      label: node.name,
      children,
    }
  }

  const items = nodes.map((node) => build(node, null)).filter(Boolean) as MenuItem[]

  return { items, submenuKeys, pathToKey, parentMap }
}

function renderIcon(icon?: string | null) {
  const Comp = resolveIcon(icon)
  return Comp ? () => h(Comp) : undefined
}

/** 根据后端菜单 icon 字段（antd 图标组件名）解析对应的图标组件。 */
function resolveIcon(icon?: string | null): Component | null {
  if (!icon) return null
  const Comp = (AntIcons as Record<string, unknown>)[icon]
  return (Comp as Component) || null
}

function restoreOpenKeys(): string[] {
  const rawKeys = localStorage.getItem(SIDEBAR_OPEN_KEYS_KEY)
  if (!rawKeys) return []

  try {
    const parsed = JSON.parse(rawKeys)
    return Array.isArray(parsed) ? parsed.filter((k): k is string => typeof k === 'string') : []
  } catch {
    localStorage.removeItem(SIDEBAR_OPEN_KEYS_KEY)
    return []
  }
}

function handleMenuClick(info: MenuInfo) {
  const path = String(info.key)
  if (!path || path === route.path) return

  if (isExternal(path)) {
    window.open(path, '_blank', 'noopener,noreferrer')
    return
  }

  router.push(path)
}
</script>
