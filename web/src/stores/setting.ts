import { defineStore } from 'pinia'
import settings from '@/setting'
import { getBranding } from '@/api/branding'

type SettingsKeys = keyof typeof settings
type ThemeMode = 'light' | 'dark' | 'system'

const THEME_MODE_KEY = 'mori_admin_theme_mode'

function readThemeMode(): ThemeMode {
  const storedMode = localStorage.getItem(THEME_MODE_KEY)
  return storedMode === 'dark' || storedMode === 'light' || storedMode === 'system'
    ? storedMode
    : settings.themeMode
}

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    ...settings,
    themeMode: readThemeMode(),
    logoRevision: 0,
    systemDark: window.matchMedia('(prefers-color-scheme: dark)').matches,
  }),

  getters: {
    resolvedThemeMode(state): 'light' | 'dark' {
      return state.themeMode === 'system' ? (state.systemDark ? 'dark' : 'light') : state.themeMode
    },
  },

  actions: {
    applyLogo(logo: string | null) {
      this.logo = logo || settings.logo
      this.logoRevision += 1
    },

    async refreshLogo() {
      const revision = this.logoRevision
      const result = await getBranding()
      if (result.ok && result.data && revision === this.logoRevision) {
        this.applyLogo(result.data.logo)
      }
      return result
    },

    changeSetting(key: SettingsKeys, value: (typeof settings)[SettingsKeys]) {
      if (Object.prototype.hasOwnProperty.call(this, key)) {
        this[key] = value as never
        if (key === 'themeMode') {
          localStorage.setItem(THEME_MODE_KEY, String(value))
        }
      }
    },

    setThemeMode(mode: ThemeMode) {
      this.themeMode = mode
      localStorage.setItem(THEME_MODE_KEY, mode)
    },
  },
})
