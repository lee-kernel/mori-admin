<template>
  <section class="page-filter-bar" aria-label="页面筛选">
    <div class="page-filter-bar-row">
      <div class="page-filter-bar-basic">
        <slot name="basic" />
        <div v-if="$slots.submit" class="page-filter-bar-submit"><slot name="submit" /></div>
      </div>
      <div v-if="hasAdvanced || $slots.extra" class="page-filter-bar-extra">
        <a-button
          v-if="hasAdvanced"
          :aria-expanded="expanded"
          :aria-controls="advancedId"
          @click="expanded = !expanded">
          {{ expanded ? '收起' : '展开' }}{{ advancedLabel }}
        </a-button>
        <slot name="extra" />
      </div>
    </div>
    <div
      v-if="hasAdvanced"
      :id="advancedId"
      class="page-filter-bar-advanced-collapse"
      :class="{ 'is-expanded': expanded }"
      :aria-hidden="!expanded">
      <div class="page-filter-bar-advanced-inner">
        <div class="page-filter-bar-advanced">
          <slot name="advanced" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, useId, useSlots } from 'vue'

const props = withDefaults(
  defineProps<{
    advanced?: boolean
    advancedLabel?: string
  }>(),
  { advanced: false, advancedLabel: '高级筛选' }
)

const expanded = defineModel<boolean>('expanded', { default: false })
const slots = useSlots()
const advancedId = useId()
const hasAdvanced = computed(() => props.advanced && Boolean(slots.advanced))
</script>

<style scoped lang="scss">
.page-filter-bar {
  min-width: 0;
  container: page-filter / inline-size;
}

.page-filter-bar-row,
.page-filter-bar-basic,
.page-filter-bar-submit,
.page-filter-bar-extra,
.page-filter-bar-advanced {
  display: flex;
  gap: 8px;
  align-items: center;
  min-width: 0;
}

.page-filter-bar-row,
.page-filter-bar-basic,
.page-filter-bar-advanced {
  flex-wrap: wrap;
}

.page-filter-bar-basic {
  flex: 1 1 0;
}

.page-filter-bar-basic :deep(> :is(.ant-input, .ant-input-affix-wrapper)) {
  flex: 0 1 auto;
  width: 120px;
  min-width: 100px;
}

.page-filter-bar-basic :deep(> :is(.ant-input-group-wrapper, .page-filter-search)) {
  flex: 1 1 200px;
  min-width: min(200px, 100%);
  max-width: 360px;
}

.page-filter-bar-basic :deep(> .ant-select) {
  flex: 0 1 auto;
  width: 120px;
  min-width: 110px;
}

.page-filter-bar-basic :deep(> .tag-filter) {
  flex: 0 1 auto;
  width: 180px;
  min-width: 150px;
}

.page-filter-bar-basic :deep(> .ant-picker) {
  flex: 0 1 auto;
  width: 320px;
  min-width: 260px;
}

.page-filter-bar-submit {
  flex: 0 0 auto;
}

.page-filter-bar-extra {
  flex: 0 0 auto;
  flex-wrap: wrap;
  justify-content: flex-end;
  margin-inline-start: auto;
}

.page-filter-bar-advanced-collapse {
  display: grid;
  grid-template-rows: 0fr;
  visibility: hidden;
  opacity: 0;
  transition:
    grid-template-rows var(--mori-admin-motion-base) var(--mori-admin-ease-standard),
    opacity var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    visibility var(--mori-admin-motion-base) var(--mori-admin-ease-standard);

  &.is-expanded {
    grid-template-rows: 1fr;
    visibility: visible;
    opacity: 1;
  }
}

.page-filter-bar-advanced-inner {
  min-height: 0;
  overflow: hidden;
}

.page-filter-bar-advanced {
  padding-top: 8px;
}

@container page-filter (width < 640px) {
  .page-filter-bar-basic {
    flex: 1 1 100%;
  }

  .page-filter-bar-basic :deep(> :not(.page-filter-bar-submit)) {
    flex: 1 1 100%;
    width: 100%;
    min-width: 0;
    max-width: none;
  }

  .page-filter-bar-submit {
    flex: 1 1 100%;
  }
}
</style>
