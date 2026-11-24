// src/hooks/useResizeHandler.ts
import { onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { storeToRefs } from 'pinia'
import layoutVariables from '@/styles/variables.module.scss'

const sidebarCollapseBreakpoint = Number.parseFloat(layoutVariables.sidebarCollapseBreakpoint)

/**
 * Layout 响应式处理 Hook
 * - 监听窗口大小变化
 * - 自动切换 mobile / desktop
 * - 自动关闭侧边栏
 */
export function useResizeHandler() {
  const route = useRoute()
  const appStore = useAppStore()

  const { device, sidebar } = storeToRefs(appStore)

  /** 是否为移动端 */
  const isMobile = () => window.innerWidth < sidebarCollapseBreakpoint

  let resizeRaf = 0

  /** 窗口大小变化处理（rAF 节流，避免高频触发） */
  const resizeHandler = () => {
    if (resizeRaf) return
    resizeRaf = window.requestAnimationFrame(() => {
      resizeRaf = 0
      if (!document.hidden) {
        const mobile = isMobile()
        appStore.toggleDevice(mobile ? 'mobile' : 'desktop')

        if (mobile) {
          appStore.closeSidebar(true)
        }
      }
    })
  }

  /** 监听路由变化时关闭侧边栏（与旧 mixin 一致） */
  watch(
    () => route.fullPath,
    () => {
      if (device.value === 'mobile' && sidebar.value.opened) {
        appStore.closeSidebar(false)
      }
    }
  )

  /** 生命周期 */
  onMounted(() => {
    window.addEventListener('resize', resizeHandler)

    // 初次判断设备类型
    if (isMobile()) {
      appStore.toggleDevice('mobile')
      appStore.closeSidebar(true)
    }
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeHandler)
    if (resizeRaf) {
      window.cancelAnimationFrame(resizeRaf)
    }
  })
}
