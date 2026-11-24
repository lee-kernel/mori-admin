import type { RouteRecordRaw } from 'vue-router'
import type { MenuNode } from '@/api/menu'
import { resolveComponent } from '@/router/component-map'

/**
 * 将后端下发的菜单树转换为 vue-router 路由配置。
 *
 * 规则：
 * - 顶层菜单作为顶层路由；其下级作为 children。
 * - component 解析失败（未找到对应视图）则丢弃该节点（其子节点也一并丢弃）。
 * - 子路由 path 采用「相对父路径」的写法，避免与父级嵌套冲突。
 */
export function buildRoutesFromMenus(menus: MenuNode[]): RouteRecordRaw[] {
  return menus
    .map((menu) => buildRoute(menu, ''))
    .filter((route): route is RouteRecordRaw => Boolean(route))
}

/**
 * 构建单个路由节点。
 * @param menu       菜单节点
 * @param parentPath 父节点的绝对路径（顶层为空串），用于计算子路由的相对 path
 */
function buildRoute(menu: MenuNode, parentPath: string): RouteRecordRaw | null {
  const component = resolveComponent(menu.component)
  if (!component) return null

  // 顶层路由使用绝对路径；非顶层路由使用相对父级的剩余 path 片段
  const isTopLevel = parentPath === ''
  const path = isTopLevel ? menu.path : relativeChildPath(parentPath, menu.path)

  const route: RouteRecordRaw = {
    path,
    name: routeNameOf(menu),
    component: component as RouteRecordRaw['component'],
    meta: {
      menuId: menu.id,
      permissionKey: menu.permission_key,
      title: menu.name,
      icon: menu.icon || undefined,
      hidden: menu.hidden,
      isExternal: menu.is_external,
    },
  }

  if (menu.redirect) {
    route.redirect = menu.redirect
  }

  const childRoutes = (menu.children || [])
    .map((child) => buildRoute(child, menu.path))
    .filter((r): r is RouteRecordRaw => Boolean(r))

  if (childRoutes.length) {
    route.children = childRoutes
  }

  return route
}

/**
 * 根据父路径，计算子菜单相对于父路径的 path 片段。
 * - 若子 path 以父 path 开头，去掉父 path 前缀。
 * - 否则原样返回（兼容部分菜单未按层级前缀命名的情况）。
 */
function relativeChildPath(parentPath: string, childPath: string): string {
  const parent = parentPath.endsWith('/') ? parentPath : parentPath + '/'
  if (childPath.startsWith(parent)) {
    return childPath.slice(parent.length)
  }
  // 子路径不以父路径开头时，去掉开头的 "/" 让 vue-router 视作相对路径
  return childPath.replace(/^\/+/, '')
}

function routeNameOf(menu: MenuNode): string {
  return `menu-${menu.id}`
}
