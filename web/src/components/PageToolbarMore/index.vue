<template>
  <a-dropdown v-model:open="open" trigger="click">
    <a-button :disabled="!items.length" aria-haspopup="menu" :aria-expanded="open">
      更多
      <DownOutlined aria-hidden="true" />
    </a-button>
    <template #overlay>
      <a-menu @click="handleClick">
        <a-menu-item
          v-for="item in items"
          :key="item.key"
          :danger="item.danger"
          :disabled="item.disabled">
          <component :is="item.icon" v-if="item.icon" aria-hidden="true" />
          {{ item.label }}
        </a-menu-item>
      </a-menu>
    </template>
  </a-dropdown>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Component } from 'vue'
import { DownOutlined } from '@ant-design/icons-vue'

export type PageToolbarMoreItem = {
  key: string
  label: string
  icon?: Component
  danger?: boolean
  disabled?: boolean
  onClick: () => void | Promise<void>
}

const props = defineProps<{ items: PageToolbarMoreItem[] }>()
const open = ref(false)

function handleClick({ key }: { key: string | number }) {
  const item = props.items.find((entry) => entry.key === String(key))
  if (item && !item.disabled) void item.onClick()
}
</script>
