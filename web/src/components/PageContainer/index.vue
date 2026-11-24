<template>
  <PageLayout
    class="page-layout--compat"
    :description="description"
    :scroll="table ? 'region' : 'page'"
    :show-toolbar="Boolean($slots.actions)">
    <template v-if="$slots.actions" #actions><slot name="actions" /></template>
    <slot />
  </PageLayout>
</template>

<script setup lang="ts">
import PageLayout from '@/components/PageLayout/index.vue'

/** 兼容入口；新页面直接使用 PageLayout。 */
defineProps<{
  /** 整页操作栏标题下方的功能说明。 */
  description?: string
  /** 全高表格模式关闭内容区滚动，由内部表格管理滚动。 */
  table?: boolean
}>()
</script>
