<template>
  <PageLayout title="首页" max-width="880px">
    <a-card>
      <h3 class="welcome-title">欢迎，{{ user.displayName }}</h3>
      <p class="welcome-desc">从侧栏打开你有权访问的页面。</p>
    </a-card>
  </PageLayout>
</template>

<script setup lang="ts">
import PageLayout from '@/components/PageLayout/index.vue'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
</script>

<style scoped lang="scss">
.welcome-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--ant-color-text);
}

.welcome-desc {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--ant-color-text-secondary);
}
</style>
