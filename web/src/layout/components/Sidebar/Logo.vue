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
      <h1 class="sidebar-title" :aria-hidden="collapse">{{ title }}</h1>
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
@use '@/styles/variables.module.scss' as *;

$logoSize: 28px;
$hamburgerSize: 34px;
// 侧边栏容器左右各有 1px 边框，收起态净宽为 $collapsedSideBarWidth - 2px
$collapsedLogoOffset: calc((#{$collapsedSideBarWidth} - 2px - #{$logoSize}) / 2);
$collapsedHamburgerOffset: calc((#{$collapsedSideBarWidth} - 2px - #{$hamburgerSize}) / 2);

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
    .sidebar-logo-link {
      padding-right: 0;
      padding-left: $collapsedLogoOffset;
    }

    .sidebar-title {
      max-width: 0;
      margin-left: 0;
      pointer-events: none;
      opacity: 0;
      transform: translateX(-6px);
    }

    .hamburger-container {
      right: $collapsedHamburgerOffset;
      pointer-events: none;
      opacity: 0;

      &.is-visible {
        pointer-events: auto;
        opacity: 1;
      }
    }

    &.is-hovering .sidebar-logo-link {
      pointer-events: none;
      opacity: 0;
    }
  }
}

.sidebar-logo-link {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  height: 100%;
  padding: 0 42px 0 12px;
  transition:
    padding-left var(--mori-admin-motion-slow) var(--mori-admin-ease-standard),
    padding-right var(--mori-admin-motion-slow) var(--mori-admin-ease-standard),
    opacity var(--mori-admin-motion-fast) var(--mori-admin-ease-standard);
}

.hamburger-container {
  position: absolute;
  top: 50%;
  right: 4px;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: $hamburgerSize;
  height: $hamburgerSize;
  padding: 0;
  color: var(--ant-color-text-secondary);
  cursor: pointer;
  background: transparent;
  border: 0;
  border-radius: var(--ant-border-radius);
  transform: translateY(-50%);
  transition:
    right var(--mori-admin-motion-slow) var(--mori-admin-ease-standard),
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
  width: $logoSize;
  height: $logoSize;
  vertical-align: middle;
  background: var(--ant-color-text-light-solid);
  border-radius: 4px;
}

.sidebar-logo-fallback {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: $logoSize;
  height: $logoSize;
  color: var(--ant-color-primary-text);
  background: var(--ant-color-primary-bg);
  border-radius: 4px;
}

.sidebar-title {
  flex: 1;
  min-width: 0;
  max-width: 140px;
  margin: 0 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: Avenir, 'Helvetica Neue', Arial, Helvetica, sans-serif;
  font-size: 16px;
  font-weight: 600;
  line-height: 50px;
  vertical-align: middle;
  color: var(--ant-color-text);
  white-space: nowrap;
  opacity: 1;
  transform: translateX(0);
  transition:
    opacity var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    transform var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    max-width var(--mori-admin-motion-slow) var(--mori-admin-ease-standard),
    margin-left var(--mori-admin-motion-slow) var(--mori-admin-ease-standard);
}
</style>
