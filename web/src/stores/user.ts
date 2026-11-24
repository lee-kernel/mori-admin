import { defineStore } from 'pinia'
import {
  getCurrentUser,
  login,
  logout,
  verifyLoginTwoFactor,
  type TwoFactorMethod,
  type UserProfile,
} from '@/api/auth'
import { getMyMenus, type MenuNode } from '@/api/menu'

const TOKEN_KEY = 'mori_admin_access_token'
const USER_KEY = 'mori_admin_user_profile'
// 侧边栏展开记忆按用户隔离，登出时一并清理，避免账号切换后继承上一个用户的状态
const SIDEBAR_OPEN_KEYS_KEY = 'mori_admin_sidebar_open_keys'

function readStoredUser(): UserProfile | null {
  const rawUser = localStorage.getItem(USER_KEY)
  if (!rawUser) return null

  try {
    return JSON.parse(rawUser) as UserProfile
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

interface UserState {
  token: string
  profile: UserProfile | null
  menus: MenuNode[]
  menusLoaded: boolean
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    profile: readStoredUser(),
    menus: [],
    menusLoaded: false,
  }),

  getters: {
    isLoggedIn(state) {
      return Boolean(state.token)
    },
    displayName(state) {
      return state.profile?.display_name || state.profile?.username || ''
    },
    menuPaths(state): string[] {
      return state.profile?.menu_paths || []
    },
  },

  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
    },

    setProfile(profile: UserProfile | null) {
      this.profile = profile
      if (profile) {
        localStorage.setItem(USER_KEY, JSON.stringify(profile))
      } else {
        localStorage.removeItem(USER_KEY)
      }
    },

    setMenus(menus: MenuNode[]) {
      this.menus = menus
      this.menusLoaded = true
    },

    async login(username: string, password: string) {
      const res = await login({ username, password })
      if (res.ok && res.data && !res.data.requires_2fa && res.data.access_token && res.data.user) {
        this.setToken(res.data.access_token)
        this.setProfile(res.data.user)
        this.menus = []
        this.menusLoaded = false
      }
      return res
    },

    async verifyTwoFactor(challengeToken: string, code: string, method: TwoFactorMethod = 'totp') {
      const res = await verifyLoginTwoFactor({
        challenge_token: challengeToken,
        code,
        method,
      })
      if (res.ok && res.data) {
        this.setToken(res.data.access_token)
        this.setProfile(res.data.user)
        this.menus = []
        this.menusLoaded = false
      }
      return res
    },

    async fetchProfile() {
      const res = await getCurrentUser()
      if (res.ok && res.data) {
        this.setProfile(res.data)
      }
      return res
    },

    async fetchMenus() {
      const res = await getMyMenus()
      if (res.ok && res.data) {
        this.setMenus(res.data.list)
      }
      return res
    },

    clearSession() {
      this.token = ''
      this.profile = null
      this.menus = []
      this.menusLoaded = false
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      localStorage.removeItem(SIDEBAR_OPEN_KEYS_KEY)
    },

    async logout() {
      // 登出时先调用后端登出接口以记录日志
      try {
        await logout()
      } catch (err) {
        console.error('Logout failed:', err)
      }
      this.clearSession()
    },
  },
})
