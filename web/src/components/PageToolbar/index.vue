<template>
  <div class="page-toolbar" :class="{ 'page-toolbar--with-fields': $slots.default }">
    <div v-if="displayTitle || description" class="page-toolbar-heading">
      <h2 v-if="displayTitle">{{ displayTitle }}</h2>
      <p v-if="description">{{ description }}</p>
    </div>
    <!-- 兼容旧筛选栏；新页面的筛选字段使用 PageFilterBar。 -->
    <div v-if="$slots.default" class="page-toolbar-fields"><slot /></div>
    <div v-if="$slots.actions" class="page-toolbar-actions"><slot name="actions" /></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps<{
  title?: string
  description?: string
}>()

const route = useRoute()
const displayTitle = computed(() =>
  props.title === undefined ? (route.meta.title as string) || '' : props.title
)
</script>

<style lang="scss" scoped>
@use '@/styles/variables.module.scss' as layout;

.page-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
}

.page-toolbar-heading {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 100%;
}

.page-toolbar--with-fields .page-toolbar-heading {
  flex-basis: 100%;
}

.page-toolbar-heading h2,
.page-toolbar-heading p {
  margin: 0;
}

.page-toolbar-heading h2 {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--ant-color-text);
}

.page-toolbar-heading p {
  font-size: 14px;
  line-height: 1.5;
  color: var(--ant-color-text-secondary);
}

.page-toolbar-fields,
.page-toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-width: 0;
  max-width: 100%;
}

.page-toolbar-fields {
  flex: 1 1 auto;
}

@include layout.below-sidebar-breakpoint {
  .page-toolbar-heading {
    flex-basis: 100%;
  }
}
</style>
