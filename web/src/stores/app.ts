// src/stores/app.ts
import { defineStore } from 'pinia'

/**
 * App Store（选项式）
 * 管理应用的侧边栏状态和设备信息
 * 使用 LocalStorage 替代 Cookie 进行状态持久化
 */
export const useAppStore = defineStore('app', {
  /**
   * state
   */
  state: () => ({
    /**
     * sidebar 状态
     * opened: 侧边栏是否打开
     * withoutAnimation: 切换侧边栏时是否禁用动画
     * 初始状态从 LocalStorage 读取
     */
    sidebar: {
      opened: localStorage.getItem('sidebarStatus')
        ? !!+localStorage.getItem('sidebarStatus')!
        : true,
      withoutAnimation: false,
    },
    /**
     * device 状态
     * 'desktop' | 'mobile'
     */
    device: 'desktop' as 'desktop' | 'mobile',
  }),

  /**
   * getters
   */
  getters: {
    isSidebarOpened(state) {
      return state.sidebar.opened
    },
    isMobile(state) {
      return state.device === 'mobile'
    },
  },

  /**
   * actions
   */
  actions: {
    /**
     * 切换侧边栏状态（打开/关闭）
     * 同时更新 withoutAnimation 为 false
     * 并写入 LocalStorage
     */
    toggleSidebar() {
      this.sidebar.opened = !this.sidebar.opened
      this.sidebar.withoutAnimation = false
      localStorage.setItem('sidebarStatus', this.sidebar.opened ? '1' : '0')
    },

    /**
     * 关闭侧边栏
     * @param withoutAnimation 是否禁用动画
     */
    closeSidebar(withoutAnimation: boolean) {
      this.sidebar.opened = false
      this.sidebar.withoutAnimation = withoutAnimation
      localStorage.setItem('sidebarStatus', '0')
    },

    /**
     * 设置设备类型
     * @param newDevice 'desktop' | 'mobile'
     */
    toggleDevice(newDevice: 'desktop' | 'mobile') {
      this.device = newDevice
    },
  },
})
