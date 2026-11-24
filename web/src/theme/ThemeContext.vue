<template>
  <slot />
</template>

<script setup lang="ts">
import { watchEffect } from 'vue'
import { theme } from 'ant-design-vue'
import { useSettingsStore } from '@/stores/setting'

const settingsStore = useSettingsStore()
const { token } = theme.useToken()
const browserThemeColor = Array.from(document.getElementsByTagName('meta')).find(
  (meta) => meta.name === 'theme-color'
)

// 自定义样式消费与组件相同的官方 Token，不维护独立颜色表。
watchEffect(() => {
  const style = document.documentElement.style
  for (const [name, value] of Object.entries(token.value)) {
    if (typeof value !== 'string' && typeof value !== 'number') continue
    const cssName = name.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`)
    style.setProperty(`--ant-${cssName}`, `${value}${name.startsWith('borderRadius') ? 'px' : ''}`)
  }
  style.colorScheme = settingsStore.resolvedThemeMode === 'dark' ? 'dark' : 'light'
  // 浏览器主题色与导航背景保持一致，避免打开侧栏时改变浏览器栏的配色。
  if (browserThemeColor) browserThemeColor.content = token.value.colorBgContainer
})
</script>
