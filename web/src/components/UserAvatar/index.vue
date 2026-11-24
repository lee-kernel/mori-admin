<template>
  <a-avatar
    class="user-avatar"
    :size="size"
    :alt="`${userStore.displayName || '用户'}的头像`"
    :draggable="false">
    {{ initial }}
  </a-avatar>
</template>

<script setup lang="ts">
/** 当前登录用户头像；使用显示名称首字母。 */
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

withDefaults(defineProps<{ size?: number }>(), { size: 34 })
const userStore = useUserStore()
const initial = computed(() => (userStore.displayName || '?').slice(0, 1).toUpperCase())
</script>

<style scoped lang="scss">
.user-avatar {
  flex: 0 0 auto;
  font-weight: 600;
  color: var(--ant-color-primary-text);
  background: var(--ant-color-primary-bg);
}
</style>
