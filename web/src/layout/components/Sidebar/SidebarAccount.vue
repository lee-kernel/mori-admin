<template>
  <div class="sidebar-account" :class="{ collapse }">
    <a-dropdown placement="topLeft" trigger="click">
      <button class="account-trigger" type="button" aria-label="打开账户菜单">
        <UserAvatar :size="32" />
        <span class="account-name" :aria-hidden="collapse">{{ displayName || '用户' }}</span>
      </button>

      <template #overlay>
        <div class="account-menu" role="menu" @click.stop>
          <div class="account-summary">
            <UserAvatar :size="40" />
            <div class="account-identity">
              <strong>{{ displayName || '用户' }}</strong>
              <span v-if="profile?.email">{{ profile.email }}</span>
            </div>
          </div>

          <a-menu :selectable="false" @click="handleUserCommand">
            <a-menu-item key="profile">
              <span class="menu-item-content">
                <UserOutlined />
                <span>个人中心</span>
              </span>
            </a-menu-item>
            <a-menu-item key="security">
              <span class="menu-item-content">
                <SafetyOutlined />
                <span>安全设置</span>
              </span>
            </a-menu-item>
            <a-sub-menu key="theme">
              <template #title>
                <span class="menu-item-content">
                  <SkinOutlined />
                  <span>外观：{{ themeLabel }}</span>
                </span>
              </template>
              <a-menu-item key="light" :disabled="themeMode === 'light'">
                <span class="menu-item-content">
                  <BulbOutlined />
                  <span>浅色</span>
                </span>
              </a-menu-item>
              <a-menu-item key="dark" :disabled="themeMode === 'dark'">
                <span class="menu-item-content">
                  <BulbFilled />
                  <span>深色</span>
                </span>
              </a-menu-item>
              <a-menu-item key="system" :disabled="themeMode === 'system'">
                <span class="menu-item-content">
                  <DesktopOutlined />
                  <span>跟随系统</span>
                </span>
              </a-menu-item>
            </a-sub-menu>
            <a-menu-divider />
            <a-menu-item key="logout" danger>
              <span class="menu-item-content">
                <LogoutOutlined />
                <span>退出登录</span>
              </span>
            </a-menu-item>
          </a-menu>
        </div>
      </template>
    </a-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import type { MenuInfo } from 'ant-design-vue/es/menu/src/interface'
import {
  BulbFilled,
  BulbOutlined,
  DesktopOutlined,
  LogoutOutlined,
  SafetyOutlined,
  SkinOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import UserAvatar from '@/components/UserAvatar/index.vue'
import { useSettingsStore } from '@/stores/setting'
import { useUserStore } from '@/stores/user'

defineProps<{ collapse: boolean }>()

const router = useRouter()
const settingsStore = useSettingsStore()
const userStore = useUserStore()
const { themeMode } = storeToRefs(settingsStore)
const { displayName, profile } = storeToRefs(userStore)
const themeLabel = computed(
  () => ({ light: '浅色', dark: '深色', system: '跟随系统' })[themeMode.value]
)

async function handleUserCommand(info: MenuInfo) {
  if (info.key === 'profile') {
    router.push('/account/profile')
    return
  }

  if (info.key === 'security') {
    router.push('/account/security')
    return
  }

  if (info.key === 'light' || info.key === 'dark' || info.key === 'system') {
    settingsStore.setThemeMode(info.key)
    return
  }

  if (info.key === 'logout') {
    await userStore.logout()
    router.replace('/login')
  }
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.module.scss' as *;

$accountPaddingX: 10px;
$avatarSize: 32px;
// 侧边栏左右各 1px 边框，收起态 .account-trigger 宽为 $collapsedSideBarWidth - 2px - 2 * $accountPaddingX
$collapsedTriggerPaddingX: calc(
  (#{$collapsedSideBarWidth} - 2px - #{$accountPaddingX} * 2 - #{$avatarSize}) / 2
);

.sidebar-account {
  flex: 0 0 auto;
  padding: 10px $accountPaddingX;
  border-top: 1px solid var(--ant-color-border-secondary);
  transition: border-color var(--mori-admin-motion-base) var(--mori-admin-ease-standard);

  &.collapse {
    .account-trigger {
      padding-right: $collapsedTriggerPaddingX;
      padding-left: $collapsedTriggerPaddingX;
    }

    .account-name {
      max-width: 0;
      margin-left: 0;
      pointer-events: none;
      opacity: 0;
      transform: translateX(-6px);
    }
  }
}

.account-trigger {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  padding: 6px 8px;
  overflow: hidden;
  color: var(--ant-color-text);
  text-align: left;
  cursor: pointer;
  background: transparent;
  border: 0;
  border-radius: var(--ant-border-radius);
  transition:
    padding-left var(--mori-admin-motion-slow) var(--mori-admin-ease-standard),
    padding-right var(--mori-admin-motion-slow) var(--mori-admin-ease-standard),
    background-color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard);

  &:hover {
    background: var(--ant-color-fill-tertiary);
  }

  &:focus-visible {
    outline: 2px solid var(--ant-color-primary);
    outline-offset: 2px;
  }
}

.account-name {
  flex: 1;
  min-width: 0;
  max-width: 130px;
  margin-left: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
  white-space: nowrap;
  opacity: 1;
  transform: translateX(0);
  transition:
    opacity var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    transform var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    max-width var(--mori-admin-motion-slow) var(--mori-admin-ease-standard),
    margin-left var(--mori-admin-motion-slow) var(--mori-admin-ease-standard);
}

.account-menu {
  width: 232px;
  overflow: hidden;
  background: var(--ant-color-bg-elevated);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: var(--ant-border-radius-lg);
  box-shadow: var(--ant-box-shadow-secondary);
}

.menu-item-content {
  display: inline-flex;
  gap: 10px;
  align-items: center;
}

.account-summary {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 14px;
  background: var(--ant-color-fill-quaternary);
}

.account-identity {
  display: grid;
  min-width: 0;

  strong,
  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  span {
    margin-top: 2px;
    font-size: 12px;
    color: var(--ant-color-text-secondary);
  }
}
</style>
