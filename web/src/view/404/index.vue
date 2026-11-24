<template>
  <div class="not-found-container">
    <div class="error-content">
      <div class="error-code">404</div>
      <h2 class="error-message">页面不存在</h2>
      <p class="error-detail">找不到您访问的资源，请检查网址是否正确或返回首页。</p>
      <a-button type="primary" size="large" class="home-button" @click="goBackHome">
        <template #icon><ArrowLeftOutlined /></template>
        返回首页
      </a-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router'
import { ArrowLeftOutlined } from '@ant-design/icons-vue'

const router = useRouter()

function goBackHome() {
  router.push('/')
}
</script>

<style scoped>
.not-found-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: var(--mori-admin-viewport-height);
  padding: calc(20px + var(--mori-admin-safe-top)) calc(20px + var(--mori-admin-safe-right))
    calc(20px + var(--mori-admin-safe-bottom)) calc(20px + var(--mori-admin-safe-left));
  background-color: var(--ant-color-bg-layout);
}

.error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 440px;
  padding: 40px 28px;
  text-align: center;
  background-color: var(--ant-color-bg-container);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: var(--mori-admin-radius-surface);
}

.error-code {
  margin-bottom: 12px;
  font-size: 72px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  color: var(--ant-color-primary);
  letter-spacing: -0.02em;
}

.error-message {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--ant-color-text);
}

.error-detail {
  margin: 0 0 24px;
  font-size: 14px;
  line-height: 1.5;
  color: var(--ant-color-text-secondary);
}

.home-button {
  min-width: 140px;
}
</style>
