<template>
  <a-tooltip title="刷新">
    <a-button shape="circle" :loading="loading" aria-label="刷新" @click="emit('click')">
      <template #icon><ReloadOutlined /></template>
    </a-button>
  </a-tooltip>
</template>

<script setup lang="ts">
import { ReloadOutlined } from '@ant-design/icons-vue'

defineProps<{ loading?: boolean }>()
const emit = defineEmits<{ click: [] }>()
</script>
