<template>
  <section class="card-grid-section">
    <div ref="scrollElement" class="card-grid-section-scroll"><slot /></div>
    <div v-if="$slots.footer" class="card-grid-section-footer"><slot name="footer" /></div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const scrollElement = ref<globalThis.HTMLElement | null>(null)
defineExpose({ scrollToTop: () => scrollElement.value?.scrollTo({ top: 0 }) })
</script>

<style scoped lang="scss">
.card-grid-section {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.card-grid-section-scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.card-grid-section-footer {
  display: flex;
  flex: 0 0 auto;
  justify-content: flex-end;
  padding-top: var(--mori-admin-section-gap);
}
</style>
