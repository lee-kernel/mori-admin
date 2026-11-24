import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { constantRoute, FALLBACK_ROUTE } from '@/router/routes'
import { buildRoutesFromMenus } from '@/router/dynamic'
import { PREVIEW_MENUS, PREVIEW_PROFILE } from '@/router/preview-menus'
import { useUserStore } from '@/stores/user'
import type { MenuNode } from '@/api/menu'
import { message } from 'ant-design-vue'

const IS_UI_PREVIEW = import.meta.env.VITE_UI_PREVIEW === 'true'

/** 登录页路径常量 */
const LOGIN_PATH = '/login'
/** 404 页路径常量 */
const NOT_FOUND_PATH = '/404'
const router = createRouter({
  history: createWebHashHistory(),
  routes: [...constantRoute, FALLBACK_ROUTE],
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition || { left: 0, top: 0 }
  },
})

/** 识别浏览器加载异步页面资源失败，避免把其他错误当作版本更新。 */
function isPageLoadError(error: unknown): boolean {
  return (
    error instanceof Error &&
    /failed to fetch dynamically imported module|error loading dynamically imported module|importing a module script failed|loading chunk [\w-]+ failed/i.test(
      error.message
    )
  )
}

router.onError((error) => {
  if (isPageLoadError(error)) {
    message.warning('页面加载失败，可能有新版本或网络异常。请先保存未提交的内容，再刷新页面。', 8)
  }
})

/**
 * 将后端下发的菜单转换后的路由列表动态注册到 router。
 * 重复调用时会先清理上一次注册的动态路由，避免菜单刷新后出现重复或残留路由。
 */
function registerDynamicRoutes(menuRoutes: RouteRecordRaw[]) {
  // 常量路由 + fallback 不能被清理，其余的视为「动态路由」予以移除
  const preservedNames = new Set<string | symbol>(
    constantRoute.map((r) => r.name).filter(Boolean) as (string | symbol)[]
  )
  if (FALLBACK_ROUTE.name) {
    preservedNames.add(FALLBACK_ROUTE.name)
  }

  for (const route of router.getRoutes()) {
    if (route.name && !preservedNames.has(route.name)) {
      router.removeRoute(route.name)
    }
  }

  for (const route of menuRoutes) {
    router.addRoute(route)
  }
}

/** 将已刷新的菜单树立即同步到路由表，供菜单和用户组管理页复用。 */
function syncDynamicRoutes(menus: MenuNode[]) {
  registerDynamicRoutes(buildRoutesFromMenus(menus))
}

/**
 * 确保当前会话的「用户信息」和「菜单数据」已加载，并据此完成动态路由注册。
 * 任一步骤失败返回 false，调用方应做登出处理。
 */
async function ensureUserAndMenus(userStore: ReturnType<typeof useUserStore>): Promise<boolean> {
  if (!userStore.profile) {
    const res = await userStore.fetchProfile()
    if (!res.ok) return false
  }
  if (!userStore.menusLoaded) {
    const res = await userStore.fetchMenus()
    if (!res.ok) return false
    syncDynamicRoutes(userStore.menus)
  }
  return true
}

/**
 * 全局前置守卫：
 * 1. 登录/404 直接放行（其中登录页若已登录则跳首页）；
 * 2. 未登录跳转登录页并回填 redirect；
 * 3. 已登录但菜单未加载时，先拉取菜单 + 注册动态路由，再重定向到目标路由；
 * 4. 已登录且菜单已加载，若目标路由匹配不到则跳 404。
 */
router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()

  // 纯前端 UI 预览模式：无需后端鉴权，直接注册内置范例菜单与本地身份
  if (IS_UI_PREVIEW) {
    if (!userStore.menusLoaded) {
      if (!userStore.profile) {
        userStore.profile = PREVIEW_PROFILE
      }
      userStore.setMenus(PREVIEW_MENUS)
      syncDynamicRoutes(PREVIEW_MENUS)
      next({
        path: to.path === LOGIN_PATH ? '/' : to.path,
        query: to.query,
        hash: to.hash,
        replace: true,
      })
      return
    }
    if (to.path === LOGIN_PATH) {
      next('/')
      return
    }
    if (to.name === FALLBACK_ROUTE.name) {
      next({ path: NOT_FOUND_PATH, replace: true })
      return
    }
    next()
    return
  }

  // 1. 登录页：已登录直接进首页，未登录正常进入
  if (to.path === LOGIN_PATH) {
    next(userStore.isLoggedIn ? '/' : undefined)
    return
  }

  // 1. 404 页：直接放行，避免出现死循环
  if (to.path === NOT_FOUND_PATH) {
    next()
    return
  }

  // 2. 未登录：强制跳转登录页
  if (!userStore.isLoggedIn) {
    next({ path: LOGIN_PATH, query: { redirect: to.fullPath } })
    return
  }

  // 3. 菜单尚未加载：先拉取并注册动态路由，再重新进入目标路由
  if (!userStore.menusLoaded) {
    const ok = await ensureUserAndMenus(userStore)
    if (!ok) {
      userStore.clearSession()
      next({ path: LOGIN_PATH, query: { redirect: to.fullPath } })
      return
    }
    // replace: true 避免在历史栈里留下一条「中间态」记录
    next({ path: to.path, query: to.query, hash: to.hash, replace: true })
    return
  }

  // 4. 未匹配到任何路由（fallback 触发）→ 404
  if (to.name === FALLBACK_ROUTE.name) {
    next({ path: NOT_FOUND_PATH, replace: true })
    return
  }

  next()
})

export { syncDynamicRoutes }
export default router
