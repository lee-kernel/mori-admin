<template>
  <a-card class="table-section">
    <slot />
    <div v-if="$slots.footer" class="table-footer"><slot name="footer" /></div>
  </a-card>
</template>

<style lang="scss" scoped>
@use '@/styles/table.scss' as *;
</style>
