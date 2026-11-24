<template>
  <div :class="layoutClass" class="app-wrapper">
    <Transition name="fade">
      <div v-if="showMobileMask" class="drawer-bg" @click="closeMobileSidebar" />
    </Transition>

    <Sidebar class="sidebar-container" />

    <div class="main-container">
      <div class="main-surface">
        <div class="mobile-navigation">
          <button
            type="button"
            :aria-label="sidebar.opened ? '收起侧边栏' : '打开侧边栏'"
            @click="appStore.toggleSidebar()">
            <MenuFoldOutlined v-if="sidebar.opened" />
            <MenuUnfoldOutlined v-else />
          </button>
        </div>
        <TagsView v-if="showTabs" />
        <AppMain />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'
import { useAppStore } from '@/stores/app'
import { useSettingsStore } from '@/stores/setting'
import { useResizeHandler } from '@/hooks/useResizeHandler'
import { AppMain, Sidebar, TagsView } from './components'

const appStore = useAppStore()
const settingsStore = useSettingsStore()
const { sidebar, device } = storeToRefs(appStore)
const { showTabs } = storeToRefs(settingsStore)

useResizeHandler()

const showMobileMask = computed(() => device.value === 'mobile' && sidebar.value.opened)

const layoutClass = computed(() => ({
  hideSidebar: !sidebar.value.opened,
  openSidebar: sidebar.value.opened,
  withoutAnimation: sidebar.value.withoutAnimation,
  mobile: device.value === 'mobile',
}))

function closeMobileSidebar() {
  appStore.closeSidebar(false)
}
</script>

<style lang="scss" scoped>
@use '@/styles/mixin.scss' as *;
@use '@/styles/variables.module.scss' as *;

.app-wrapper {
  @include clearfix;

  position: relative;
  width: 100%;
  height: var(--mori-admin-viewport-height);
  overflow: hidden;
  background: var(--ant-color-bg-layout);
  transition: background-color var(--mori-admin-motion-base) var(--mori-admin-ease-standard);
}

.drawer-bg {
  position: absolute;
  inset: var(--mori-admin-safe-top) var(--mori-admin-safe-right) var(--mori-admin-safe-bottom)
    var(--mori-admin-safe-left);
  z-index: var(--mori-admin-z-sidebar-mask);
  background: rgb(0 0 0 / 30%);
}

:global(.main-container) {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: calc(var(--mori-admin-safe-top) + var(--mori-admin-shell-gap))
    calc(var(--mori-admin-safe-right) + var(--mori-admin-shell-gap))
    calc(var(--mori-admin-safe-bottom) + var(--mori-admin-shell-gap)) 0;
  overflow: hidden;
}

.main-surface {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--ant-color-bg-container);
  border-radius: var(--mori-admin-radius-surface);
  transition: background-color var(--mori-admin-motion-base) var(--mori-admin-ease-standard);
}

.mobile-navigation {
  display: none;
}

@include below-sidebar-breakpoint {
  :global(.main-container) {
    padding-left: calc(var(--mori-admin-safe-left) + var(--mori-admin-shell-gap));
  }

  .mobile-navigation {
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    height: 44px;
    padding: 0 var(--mori-admin-page-padding);
    background: var(--ant-color-bg-container);
    border-bottom: 1px solid var(--ant-color-border-secondary);
  }

  .mobile-navigation button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    color: var(--ant-color-text-secondary);
    cursor: pointer;
    background: transparent;
    border: 0;
    border-radius: var(--ant-border-radius);
    transition:
      color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
      background-color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard);
  }

  .mobile-navigation button:hover {
    color: var(--ant-color-text);
    background: var(--ant-color-fill-tertiary);
  }

  .mobile-navigation button:focus-visible {
    outline: 2px solid var(--ant-color-primary);
    outline-offset: 2px;
  }
}
</style>
