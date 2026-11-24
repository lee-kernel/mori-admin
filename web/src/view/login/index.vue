<template>
  <main class="login-page">
    <section class="login-shell">
      <section
        class="brand-panel"
        :class="{ 'brand-panel--dark': settingsStore.resolvedThemeMode === 'dark' }"
        aria-label="后台介绍">
        <header class="brand-copy">
          <img v-if="settingsStore.logo" :src="settingsStore.logo" alt="" />
          <strong>{{ settingsStore.title }}</strong>
        </header>
        <span class="orb orb--one" aria-hidden="true" />
        <span class="orb orb--two" aria-hidden="true" />
        <span class="orb orb--three" aria-hidden="true" />
        <span class="orb orb--four" aria-hidden="true" />
        <span class="orb orb--five" aria-hidden="true" />
        <aside class="glass-card">
          <SafetyCertificateOutlined aria-hidden="true" />
          <div>
            <strong>安全进入管理后台</strong>
            <span>登录后，你可以访问获授权的菜单。</span>
          </div>
        </aside>
      </section>

      <div class="auth-panel">
        <a-form
          v-if="step === 'credentials'"
          class="login-form"
          layout="vertical"
          method="post"
          :model="loginForm"
          :rules="loginRules"
          :required-mark="false"
          @finish="signIn">
          <header class="form-header">
            <h1>{{ settingsStore.title }}</h1>
            <p>使用你的账号登录管理后台</p>
          </header>

          <a-form-item name="username">
            <a-input
              id="username"
              v-model:value="loginForm.username"
              name="username"
              aria-label="用户名"
              autocorrect="off"
              autocapitalize="none"
              :spellcheck="false"
              required
              size="large"
              placeholder="输入用户名"
              autocomplete="username">
              <template #prefix>
                <UserOutlined />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item name="password">
            <a-input-password
              id="current-password"
              v-model:value="loginForm.password"
              name="password"
              aria-label="密码"
              enterkeyhint="go"
              required
              size="large"
              placeholder="输入密码"
              autocomplete="current-password">
              <template #prefix>
                <LockOutlined />
              </template>
            </a-input-password>
          </a-form-item>

          <a-button
            class="login-button"
            type="primary"
            size="large"
            html-type="submit"
            :loading="loading">
            登录
          </a-button>

          <a-alert v-if="error" type="error" :message="error" show-icon role="alert" />

          <p class="security-note">
            <SafetyCertificateOutlined />
            <span>凭据仅用于身份验证，系统不会在页面中保存你的密码。</span>
          </p>
        </a-form>

        <a-form
          v-else
          class="login-form"
          layout="vertical"
          :model="twoFactorForm"
          :rules="twoFactorRules"
          :required-mark="false"
          @finish="verifyTwoFactor">
          <header class="form-header">
            <h1>双因素认证</h1>
            <p>
              {{
                twoFactorMethod === 'totp'
                  ? '请输入验证器应用中的 6 位动态验证码'
                  : '请输入备用的一次性恢复码（如 ABCD-EFGH）'
              }}
            </p>
          </header>

          <a-form-item name="code">
            <a-input
              id="two-factor-code"
              v-model:value="twoFactorForm.code"
              name="code"
              :aria-label="twoFactorMethod === 'totp' ? '6 位动态验证码' : '一次性恢复码'"
              :inputmode="twoFactorMethod === 'totp' ? 'numeric' : 'text'"
              :autocomplete="twoFactorMethod === 'totp' ? 'one-time-code' : 'off'"
              :maxlength="twoFactorMethod === 'totp' ? 6 : 16"
              autocorrect="off"
              autocapitalize="characters"
              :spellcheck="false"
              size="large"
              :placeholder="twoFactorMethod === 'totp' ? '输入 6 位动态验证码' : '输入恢复码'">
              <template #prefix>
                <SafetyOutlined />
              </template>
            </a-input>
          </a-form-item>

          <a-button
            class="login-button"
            type="primary"
            size="large"
            html-type="submit"
            :loading="loading">
            验证并登录
          </a-button>

          <div class="two-factor-actions">
            <a-button type="link" size="small" @click="toggleTwoFactorMethod">
              {{ twoFactorMethod === 'totp' ? '使用恢复码登录' : '改用动态验证码' }}
            </a-button>
            <a-button type="link" size="small" @click="backToCredentials">返回重新登录</a-button>
          </div>

          <a-alert v-if="error" type="error" :message="error" show-icon role="alert" />

          <p class="security-note">
            <SafetyCertificateOutlined />
            <span>验证会话仅在当前页面短期有效，刷新后需重新输入密码。</span>
          </p>
        </a-form>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Rule } from 'ant-design-vue/es/form'
import {
  LockOutlined,
  SafetyCertificateOutlined,
  SafetyOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import type { TwoFactorMethod } from '@/api/auth'
import { useSettingsStore } from '@/stores/setting'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const settingsStore = useSettingsStore()
const user = useUserStore()
const step = ref<'credentials' | 'two-factor'>('credentials')
const challengeToken = ref('')
const twoFactorMethod = ref<TwoFactorMethod>('totp')
const loginForm = reactive({ username: '', password: '' })
const twoFactorForm = reactive({ code: '' })
const loginRules: Record<string, Rule[]> = {
  username: [{ required: true, whitespace: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }],
}
const twoFactorRules: Record<string, Rule[]> = {
  code: [{ required: true, whitespace: true, message: '请输入验证码' }],
}
const error = ref('')
const loading = ref(false)

async function navigateAfterLogin() {
  const redirect = route.query.redirect
  await router.replace(
    typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')
      ? redirect
      : '/'
  )
}

async function signIn() {
  if (loading.value) return
  error.value = ''
  loading.value = true
  try {
    const result = await user.login(loginForm.username.trim(), loginForm.password)
    if (!result.ok) {
      error.value = result.msg || '登录失败'
      return
    }
    if (result.data?.requires_2fa && result.data.challenge_token) {
      challengeToken.value = result.data.challenge_token
      twoFactorMethod.value = 'totp'
      twoFactorForm.code = ''
      step.value = 'two-factor'
      return
    }

    await navigateAfterLogin()
  } catch {
    error.value = '暂时无法进入后台，请重试'
  } finally {
    loginForm.password = ''
    loading.value = false
  }
}

async function verifyTwoFactor() {
  if (loading.value || !challengeToken.value) return
  error.value = ''
  loading.value = true
  try {
    const result = await user.verifyTwoFactor(
      challengeToken.value,
      twoFactorForm.code.trim(),
      twoFactorMethod.value
    )
    if (!result.ok) {
      error.value = result.msg || '验证失败'
      return
    }
    challengeToken.value = ''
    twoFactorForm.code = ''
    await navigateAfterLogin()
  } catch {
    error.value = '暂时无法完成验证，请重试'
  } finally {
    loading.value = false
  }
}

function toggleTwoFactorMethod() {
  twoFactorMethod.value = twoFactorMethod.value === 'totp' ? 'recovery' : 'totp'
  twoFactorForm.code = ''
  error.value = ''
}

function backToCredentials() {
  step.value = 'credentials'
  challengeToken.value = ''
  twoFactorForm.code = ''
  error.value = ''
}
</script>

<style lang="scss" scoped>
.login-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: var(--mori-admin-viewport-height);
  padding: calc(36px + var(--mori-admin-safe-top)) calc(32px + var(--mori-admin-safe-right))
    calc(24px + var(--mori-admin-safe-bottom)) calc(32px + var(--mori-admin-safe-left));
  font-family: 'Segoe UI Variable', 'Microsoft YaHei UI', 'PingFang SC', sans-serif;
  background:
    radial-gradient(
      circle at 12% 86%,
      color-mix(in srgb, var(--ant-color-primary) 15%, transparent),
      transparent 27rem
    ),
    radial-gradient(
      circle at 82% 12%,
      color-mix(in srgb, var(--ant-color-info) 13%, transparent),
      transparent 29rem
    ),
    radial-gradient(
      circle at 42% 25%,
      color-mix(in srgb, var(--ant-color-primary) 8%, transparent),
      transparent 23rem
    ),
    radial-gradient(
      circle at 72% 78%,
      color-mix(in srgb, var(--ant-color-info) 9%, transparent),
      transparent 25rem
    ),
    var(--ant-color-bg-layout);
}

.login-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.04fr) minmax(0, 0.96fr);
  width: min(1080px, 100%);
  min-height: min(700px, calc(var(--mori-admin-viewport-height) - 160px));
  margin: auto;
  overflow: hidden;
  background: var(--ant-color-bg-container);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 24px;
  box-shadow: 0 24px 70px color-mix(in srgb, var(--ant-color-text) 12%, transparent);
}

.brand-panel {
  position: relative;
  min-width: 0;
  min-height: 560px;
  padding: 36px;
  overflow: hidden;
  background: linear-gradient(140deg, #e2eef8 0%, #e5eef5 47%, #dae9f3 100%);
  isolation: isolate;
}

.brand-copy {
  position: relative;
  z-index: 7;
  display: grid;
  gap: 4px;
  width: max-content;
  color: var(--ant-color-text);
}

.brand-copy img {
  width: 2.5rem;
  height: 2.5rem;
  padding: 3px;
  object-fit: contain;
  background: var(--ant-color-text-light-solid);
  border-radius: 10px;
}

.brand-copy strong {
  font-size: 14px;
  letter-spacing: -0.04em;
}

.orb {
  position: absolute;
  overflow: hidden;
  pointer-events: none;
  border-radius: 50%;
}

.orb::before {
  position: absolute;
  inset: 0;
  content: '';
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--ant-color-bg-container) 38%, transparent),
    transparent 42%
  );
  border-radius: inherit;
}

.orb--one,
.orb--four,
.orb--five {
  background: color-mix(in srgb, var(--ant-color-bg-container) 13%, transparent);
  border: 1px solid color-mix(in srgb, var(--ant-color-border) 48%, transparent);
  box-shadow:
    inset 1px 1px 1px color-mix(in srgb, var(--ant-color-bg-container) 16%, transparent),
    inset -9px -10px 22px color-mix(in srgb, var(--ant-color-primary) 9%, transparent),
    0 18px 34px color-mix(in srgb, var(--ant-color-text) 8%, transparent);
  backdrop-filter: blur(5px) saturate(115%);
}

.orb--one {
  top: -23%;
  left: 18%;
  z-index: 5;
  width: 80%;
  aspect-ratio: 1;
}

.orb--two,
.orb--three {
  background: rgb(17 83 206 / 62%);
  border: 1px solid rgb(178 211 255 / 40%);
  filter: blur(3px);
  mask-image: radial-gradient(
    circle,
    #000 28%,
    rgb(0 0 0 / 80%) 48%,
    rgb(0 0 0 / 36%) 76%,
    transparent 100%
  );
}

.orb--two {
  top: 24%;
  right: -8%;
  z-index: 3;
  width: 31%;
  aspect-ratio: 1;
}

.orb--three {
  top: 43%;
  left: -14%;
  z-index: 2;
  width: 25%;
  aspect-ratio: 1;
}

.orb--three::before {
  display: none;
}

.orb--four {
  top: 43%;
  right: -40%;
  z-index: 4;
  width: 80%;
  aspect-ratio: 1;
}

.orb--five {
  bottom: -18%;
  left: -16%;
  z-index: 1;
  width: 41%;
  aspect-ratio: 1;
}

.glass-card {
  position: absolute;
  right: 28px;
  bottom: 28px;
  left: 28px;
  z-index: 6;
  display: flex;
  gap: 13px;
  align-items: center;
  padding: 17px 18px;
  color: var(--ant-color-text);
  background: color-mix(in srgb, var(--ant-color-bg-container) 56%, transparent);
  border: 1px solid color-mix(in srgb, var(--ant-color-border) 58%, transparent);
  border-radius: 18px;
  box-shadow: 0 12px 28px color-mix(in srgb, var(--ant-color-text) 12%, transparent);
  backdrop-filter: blur(18px) saturate(145%);
}

.glass-card > :first-child {
  flex: 0 0 auto;
  font-size: 22px;
  color: var(--ant-color-success);
}

.glass-card strong,
.glass-card span {
  display: block;
}

.glass-card strong {
  font-size: 13px;
}

.glass-card span {
  margin-top: 3px;
  font-size: 11px;
  line-height: 1.5;
}

.brand-panel--dark {
  background: linear-gradient(
    140deg,
    var(--ant-color-bg-layout),
    color-mix(in srgb, var(--ant-color-bg-layout) 68%, var(--ant-color-primary-bg)) 52%,
    var(--ant-color-bg-container)
  );
}

.brand-panel--dark .orb--one,
.brand-panel--dark .orb--four,
.brand-panel--dark .orb--five {
  background: color-mix(in srgb, var(--ant-color-primary-bg) 24%, transparent);
  border-color: color-mix(in srgb, var(--ant-color-text) 16%, transparent);
  box-shadow:
    inset 1px 1px 1px color-mix(in srgb, var(--ant-color-text) 12%, transparent),
    inset -9px -10px 22px color-mix(in srgb, var(--ant-color-primary) 12%, transparent),
    0 18px 34px color-mix(in srgb, var(--ant-color-bg-container) 28%, transparent);
}

.brand-panel--dark .glass-card {
  background: color-mix(in srgb, var(--ant-color-bg-container) 76%, transparent);
  border-color: color-mix(in srgb, var(--ant-color-text) 16%, transparent);
}

.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding: 52px clamp(32px, 5vw, 68px);
  background: var(--ant-color-bg-container);
}

.login-form {
  width: 100%;
  max-width: 360px;
}

.form-header {
  margin-bottom: 32px;
  text-align: center;
}

.form-header h1 {
  margin: 0;
  font-size: clamp(25px, 2.5vw, 32px);
  font-weight: 700;
  line-height: 1.2;
  color: var(--ant-color-text);
}

.form-header p {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--ant-color-text-secondary);
  white-space: nowrap;
}

:deep(.login-form .ant-input-affix-wrapper) {
  min-height: 48px;
  padding-inline: 14px;
  background: var(--ant-color-bg-container);
  border-color: var(--ant-color-border);
  border-radius: 10px;
}

:deep(.login-form .ant-input-prefix) {
  margin-inline-end: 10px;
  color: var(--ant-color-text-secondary);
}

:deep(.login-form .ant-input-affix-wrapper-focused) {
  border-color: var(--ant-color-primary);
  box-shadow: 0 0 0 3px var(--ant-color-primary-bg);
}

.login-button {
  width: 100%;
  height: 48px;
  margin-top: 4px;
  font-weight: 650;
  border-radius: 10px;
}

.two-factor-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

:deep(.login-form .ant-alert) {
  margin-top: 12px;
}

.security-note {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin: 22px 0 0;
  font-size: 11px;
  line-height: 1.6;
  color: var(--ant-color-text-secondary);
}

.security-note svg {
  flex: 0 0 auto;
  margin-top: 3px;
  color: var(--ant-color-success);
}

@media (width <= 760px) {
  .login-page {
    justify-content: flex-start;
    padding: calc(20px + var(--mori-admin-safe-top)) calc(16px + var(--mori-admin-safe-right))
      calc(28px + var(--mori-admin-safe-bottom)) calc(16px + var(--mori-admin-safe-left));
  }

  .login-shell {
    grid-template-columns: 1fr;
    min-height: 0;
    margin: 0 auto;
  }

  .brand-panel {
    min-height: 270px;
    padding: 26px;
  }

  .glass-card {
    right: 20px;
    bottom: 20px;
    left: 20px;
  }

  .auth-panel {
    padding: 38px 28px;
  }

  .login-form {
    max-width: none;
  }
}

@media (width <= 420px) {
  .auth-panel {
    padding-inline: 22px;
  }

  .form-header p {
    white-space: normal;
  }
}
</style>
