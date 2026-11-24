<template>
  <TransitionGroup name="tag-fade" tag="div" class="tags-view-container">
    <router-link
      v-for="view in visitedViews"
      :key="view.fullPath"
      :to="view.fullPath"
      class="tags-view-item"
      :class="{ active: isActive(view.fullPath) }">
      <span class="title">{{ view.title }}</span>
      <CloseOutlined class="close-icon" @click.prevent.stop="closeSelectedTag(view.fullPath)" />
    </router-link>
  </TransitionGroup>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CloseOutlined } from '@ant-design/icons-vue'
import { useTagsViewStore } from '@/stores/tagsView'

const route = useRoute()
const router = useRouter()
const tagsViewStore = useTagsViewStore()

const visitedViews = computed(() => tagsViewStore.visitedViews)

watch(
  () => route.fullPath,
  () => tagsViewStore.addVisitedView(route),
  { immediate: true }
)

function isActive(fullPath: string) {
  return route.fullPath === fullPath
}

function closeSelectedTag(fullPath: string) {
  const nextViews = tagsViewStore.delVisitedView(fullPath)
  if (!isActive(fullPath)) return

  router.push(nextViews.at(-1)?.fullPath || '/dashboard')
}
</script>

<style lang="scss" scoped>
.tags-view-container {
  display: flex;
  gap: 8px;
  align-items: center;
  width: 100%;
  height: 34px;
  padding: 0 12px;
  overflow-x: auto;
  white-space: nowrap;
  background: var(--ant-color-bg-container);
  border-bottom: 1px solid var(--ant-color-border-secondary);
  transition:
    background-color var(--mori-admin-motion-base) var(--mori-admin-ease-standard),
    border-color var(--mori-admin-motion-base) var(--mori-admin-ease-standard);

  &::-webkit-scrollbar {
    height: 5px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--ant-color-border);
    border-radius: 999px;
  }
}

.tags-view-item {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
  line-height: 24px;
  color: var(--ant-color-text-secondary);
  text-decoration: none;
  background: var(--ant-color-bg-container);
  border: 1px solid var(--ant-color-border);
  border-radius: 4px;
  transition:
    color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    background-color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    border-color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard);

  &:hover:not(.active) {
    color: var(--ant-color-text);
    background: var(--ant-color-fill-quaternary);
  }

  &.active {
    color: var(--ant-color-primary);
    background: var(--ant-color-primary-bg);
    border-color: var(--ant-color-primary);
  }
}

.close-icon {
  padding: 2px;
  font-size: 12px;
  border-radius: 50%;
  transition: background-color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard);

  &:hover {
    background: var(--ant-color-fill-secondary);
  }
}
</style>
