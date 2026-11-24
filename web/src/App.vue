<template>
  <a-config-provider :locale="zhCN" :theme="themeConfig">
    <a-app>
      <ThemeContext>
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </ThemeContext>
    </a-app>
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, watchEffect } from 'vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { useSettingsStore } from '@/stores/setting'
import { getThemeConfig } from '@/theme/config'
import ThemeContext from '@/theme/ThemeContext.vue'

const settingsStore = useSettingsStore()
const themeConfig = computed(() => getThemeConfig(settingsStore.resolvedThemeMode))

const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
const updateSystemTheme = () => {
  settingsStore.systemDark = systemTheme.matches
}
onMounted(() => {
  updateSystemTheme()
  if (import.meta.env.VITE_UI_PREVIEW !== 'true') {
    void settingsStore.refreshLogo()
  }
  systemTheme.addEventListener('change', updateSystemTheme)
})
onUnmounted(() => systemTheme.removeEventListener('change', updateSystemTheme))

watchEffect(() => {
  let icon = document.querySelector('link[data-system-logo]')
  if (!settingsStore.logo) {
    icon?.remove()
    return
  }
  if (!icon) {
    icon = document.createElement('link')
    icon.rel = 'icon'
    icon.dataset.systemLogo = ''
    document.head.append(icon)
  }
  icon.setAttribute('href', settingsStore.logo)
})
</script>
