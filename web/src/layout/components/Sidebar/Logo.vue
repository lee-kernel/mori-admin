<template>
  <div
    class="sidebar-logo-container"
    :class="{ collapse, 'without-logo': !showLogo, 'is-hovering': isHovering }"
    @mouseenter="isHovering = true"
    @mouseleave="isHovering = false">
    <router-link v-if="showLogo" class="sidebar-logo-link" to="/" :aria-label="title">
      <img v-if="logo" :src="logo" class="sidebar-logo" alt="" />
      <span v-else-if="collapse" class="sidebar-logo-fallback" aria-hidden="true">
        {{ title.slice(0, 1) }}
      </span>
      <Transition name="fade">
        <h1 v-if="!collapse" class="sidebar-title">{{ title }}</h1>
      </Transition>
    </router-link>
    <button
      class="hamburger-container"
      :class="{ 'is-visible': !collapse || isHovering }"
      type="button"
      :aria-label="collapse ? '展开侧边栏' : '收起侧边栏'"
      :title="collapse ? '展开侧边栏' : '收起侧边栏'"
      @focus="isHovering = true"
      @blur="isHovering = false"
      @click="appStore.toggleSidebar()">
      <MenuUnfoldOutlined v-if="collapse" />
      <MenuFoldOutlined v-else />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'
import { useAppStore } from '@/stores/app'
import { useSettingsStore } from '@/stores/setting'

defineProps<{
  collapse: boolean
  showLogo: boolean
}>()

const appStore = useAppStore()
const settingsStore = useSettingsStore()
const isHovering = ref(false)
const title = computed(() => settingsStore.title)
const logo = computed(() => settingsStore.logo || '')
</script>

<style lang="scss" scoped>
.sidebar-logo-container {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  height: 50px;
  overflow: hidden;
  line-height: 50px;
  background: var(--ant-color-bg-container);
  transition: background-color var(--mori-admin-motion-base) var(--mori-admin-ease-standard);

  &.collapse {
    justify-content: center;

    .sidebar-logo {
      margin-right: 0;
    }

    .sidebar-logo-link {
      position: absolute;
      inset: 0;
      justify-content: center;
      transition: opacity var(--mori-admin-motion-fast) var(--mori-admin-ease-standard);
    }

    .hamburger-container {
      position: relative;
      z-index: 1;
      pointer-events: none;
      opacity: 0;

      &.is-visible {
        pointer-events: auto;
        opacity: 1;
      }
    }

    &.is-hovering .sidebar-logo-link {
      opacity: 0;
    }
  }

  &.without-logo {
    justify-content: flex-end;
  }
}

.sidebar-logo-link {
  display: flex;
  flex: 1;
  align-items: center;
  min-width: 0;
  height: 100%;
  padding: 0 8px;
}

.hamburger-container {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  margin-right: 4px;
  color: var(--ant-color-text-secondary);
  cursor: pointer;
  background: transparent;
  border: 0;
  border-radius: var(--ant-border-radius);
  transition:
    color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    background-color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    opacity var(--mori-admin-motion-fast) var(--mori-admin-ease-standard);

  &:hover {
    color: var(--ant-color-text);
    background: var(--ant-color-fill-tertiary);
  }

  &:focus-visible {
    outline: 2px solid var(--ant-color-primary);
    outline-offset: -2px;
  }
}

.sidebar-logo {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  margin-right: 8px;
  vertical-align: middle;
  background: var(--ant-color-text-light-solid);
  border-radius: 4px;
}

.sidebar-logo-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  color: var(--ant-color-primary-text);
  background: var(--ant-color-primary-bg);
  border-radius: 4px;
}

.sidebar-title {
  flex: 1;
  min-width: 0;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: Avenir, 'Helvetica Neue', Arial, Helvetica, sans-serif;
  font-size: 16px;
  font-weight: 600;
  line-height: 50px;
  vertical-align: middle;
  color: var(--ant-color-text);
  white-space: nowrap;
}
</style>
