import { theme } from 'ant-design-vue'
import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

/** 全站主题使用官方浅色、深色算法及其派生 Token。 */
export function getThemeConfig(mode: 'light' | 'dark'): ThemeConfig {
  return {
    algorithm: mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: { borderRadius: 8 },
  }
}
