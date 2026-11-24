/**
 * 系统基础配置的类型定义
 */
export interface SettingsConfig {
  /** 系统标题 */
  title: string

  /** 系统 Logo 地址 */
  logo: string

  /** 是否固定 Header */
  fixedHeader: boolean

  /** 是否显示侧边栏 Logo */
  sidebarLogo: boolean

  /** 是否开启已开 tab 页 */
  showTabs: boolean

  /** 全站主题 */
  themeMode: 'light' | 'dark' | 'system'
}

/**
 * 默认配置
 */
const settings: SettingsConfig = {
  // 应用标题
  title: 'Mori Admin',
  logo: '',

  /** 是否固定 Header */
  fixedHeader: false,

  /** 是否显示侧边栏 Logo */
  sidebarLogo: true,

  /** 是否开启已开 tab 页 */
  showTabs: false,

  /** 全站主题 */
  themeMode: 'system',
}

export default settings
