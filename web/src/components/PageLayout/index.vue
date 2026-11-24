<template>
  <div
    class="content-inner page-layout"
    :class="[
      `page-layout--${variant}`,
      `page-layout--${scroll}`,
      variant === 'custom' && `page-layout--${preset}`,
      maxWidth && variant === 'standard' && scroll === 'page' && 'page-layout--narrow',
    ]">
    <div class="content-body" :class="{ 'content-body--table': scroll === 'region' }">
      <template v-if="variant === 'standard'">
        <PageToolbar v-if="showToolbar" :title="title" :description="description">
          <template v-if="$slots.actions" #actions><slot name="actions" /></template>
        </PageToolbar>
        <div v-if="$slots.filter" class="page-layout-filter"><slot name="filter" /></div>
      </template>
      <div class="content-body-main" :style="contentStyle"><slot /></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import PageToolbar from '@/components/PageToolbar/index.vue'

type PageLayoutProps = {
  variant?: 'standard' | 'custom'
  title?: string
  description?: string
  scroll?: 'page' | 'region'
  /** custom 变体必填。 */
  preset?: 'card' | 'canvas' | 'bleed'
  maxWidth?: string
  /** 兼容旧页面仅有 actions 时才显示整页工具栏的行为。 */
  showToolbar?: boolean
}

const props = withDefaults(defineProps<PageLayoutProps>(), {
  variant: 'standard',
  scroll: 'page',
  showToolbar: true,
})

if (props.variant === 'custom' && !props.preset) {
  throw new Error('PageLayout 的 custom 变体必须指定 preset')
}

const contentStyle = computed(() =>
  props.maxWidth &&
  (props.preset === 'card' || (props.variant === 'standard' && props.scroll === 'page'))
    ? { maxWidth: props.maxWidth }
    : undefined
)
</script>

<style scoped lang="scss">
@use '@/styles/variables.module.scss' as layout;

.page-layout--standard:not(.page-layout--compat) > .content-body {
  display: flex;
  flex-direction: column;
  gap: var(--mori-admin-section-gap);
}

.page-layout--standard:not(.page-layout--compat) :deep(.page-toolbar) {
  padding-bottom: 0;
}

.page-layout-filter {
  flex: 0 0 auto;
  min-width: 0;
}

.page-layout--region .content-body-main {
  flex: 1 1 auto;
  min-height: 0;
}

.page-layout--custom.page-layout--region .content-body-main {
  display: flex;
  flex-direction: column;
}

.page-layout--standard .content-body-main {
  min-width: 0;
}

.page-layout--standard:not(.page-layout--compat).page-layout--page .content-body-main {
  flex: 0 0 auto;
}

.page-layout--canvas > .content-body {
  background: var(--ant-color-bg-layout);
}

.page-layout--narrow .content-body-main,
.page-layout--card .content-body-main {
  width: 100%;
  margin-inline: auto;
}

.page-layout--card .content-body-main {
  max-width: 960px;
  padding: var(--mori-admin-page-padding-inline);
  background: var(--ant-color-bg-container);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: var(--mori-admin-radius-card);
}

@include layout.below-sidebar-breakpoint {
  .page-layout--card .content-body-main {
    padding: var(--mori-admin-page-padding-inline-compact);
  }
}

.page-layout--bleed > .content-body {
  padding: 0;
  overflow: hidden;
}

.page-layout--bleed .content-body-main {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-height: 0;
}
</style>
