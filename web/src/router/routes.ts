import type { RouteRecordRaw } from 'vue-router'

/**
 * 常量路由：仅包含登录、404 两个页面。
 * 业务路由全部由后端按用户权限下发，登录后通过 router.addRoute 动态注册。
 */
export const constantRoute: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/view/login/index.vue'),
    meta: { title: '登录', hidden: true },
  },
  {
    path: '/404',
    name: 'not-found',
    component: () => import('@/view/404/index.vue'),
    meta: { title: '404', hidden: true },
  },
]

/**
 * 匹配未注册路径，保留原地址供登录守卫在加载菜单后重新匹配。
 */
export const FALLBACK_ROUTE: RouteRecordRaw = {
  path: '/:pathMatch(.*)*',
  name: 'any',
  component: () => import('@/view/404/index.vue'),
  meta: { hidden: true },
}
