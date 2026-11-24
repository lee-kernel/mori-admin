<template>
  <div
    class="page-state"
    :role="kind === 'error' ? 'alert' : 'status'"
    :aria-busy="kind === 'loading'">
    <Transition name="fade-scale" mode="out-in">
      <div :key="kind" class="page-state-body">
        <template v-if="kind === 'loading'">
          <a-spin size="large" />
          <p>{{ description || '正在加载…' }}</p>
        </template>
        <template v-else-if="kind === 'empty'">
          <h3 v-if="title">{{ title }}</h3>
          <a-empty :description="description || '暂无内容'" />
          <div v-if="$slots.actions" class="page-state-actions"><slot name="actions" /></div>
        </template>
        <a-result v-else status="error" :title="title || '加载失败'" :sub-title="description">
          <template v-if="$slots.actions" #extra><slot name="actions" /></template>
        </a-result>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  kind: 'empty' | 'loading' | 'error'
  title?: string
  description?: string
}>()
</script>

<style scoped lang="scss">
.page-state {
  display: grid;
  flex: 1 1 auto;
  place-content: center;
  min-height: 240px;
  text-align: center;
}

.page-state-body {
  display: grid;
  gap: var(--mori-admin-section-gap);
  place-items: center;
}

.page-state h3,
.page-state p {
  margin: 0;
}

.page-state-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
</style>
