<template>
  <PageLayout
    title="安全设置"
    description="定期更新密码并按需开启双因素认证，进一步保护账号安全。"
    max-width="42rem">
    <div class="security-sections">
      <a-card title="修改密码">
        <a-form layout="vertical" :model="form" @finish="save">
          <a-form-item
            name="currentPassword"
            label="当前密码"
            :rules="[{ required: true, message: '请输入当前密码' }]">
            <a-input-password
              v-model:value="form.currentPassword"
              autocomplete="current-password" />
          </a-form-item>
          <a-form-item
            name="newPassword"
            label="新密码"
            :rules="[{ required: true, min: 12, message: '请输入至少 12 个字符的新密码' }]">
            <a-input-password
              v-model:value="form.newPassword"
              autocomplete="new-password"
              :maxlength="256" />
          </a-form-item>
          <a-button type="primary" html-type="submit" :loading="saving">修改密码</a-button>
        </a-form>
      </a-card>

      <a-card title="双因素认证（2FA）" :loading="twoFactorLoading">
        <template #extra>
          <a-tag :color="twoFactorStatus.enabled ? 'success' : 'default'">
            {{ twoFactorStatus.enabled ? '已开启' : '未开启' }}
          </a-tag>
        </template>

        <template v-if="!twoFactorStatus.enabled">
          <p class="section-desc">
            开启后，登录时除密码外还需输入验证器应用生成的 6 位动态验证码（支持 Google
            Authenticator、Microsoft Authenticator、1Password 等）。
          </p>
          <a-button type="primary" @click="openSetupModal">开启双因素认证</a-button>
        </template>

        <template v-else>
          <a-descriptions :column="1" size="small" class="status-descriptions">
            <a-descriptions-item label="开启时间">
              {{ formatTimestamp(twoFactorStatus.enabled_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="可用恢复码">
              <span>{{ twoFactorStatus.recovery_codes_remaining }} 组</span>
              <span v-if="twoFactorStatus.recovery_codes_remaining <= 2" class="low-code-tip">
                （数量偏少，建议重新生成）
              </span>
            </a-descriptions-item>
          </a-descriptions>

          <a-space wrap class="status-actions">
            <a-button @click="openRegenerateModal">重新生成恢复码</a-button>
            <a-button danger @click="openDisableModal">关闭双因素认证</a-button>
          </a-space>
        </template>
      </a-card>
    </div>

    <a-modal
      v-model:open="setupModalOpen"
      title="开启双因素认证"
      width="480px"
      :mask-closable="false"
      :footer="null"
      @cancel="closeSetupModal">
      <template v-if="setupStep === 'password'">
        <p class="modal-tip">请先验证当前密码，以生成专属的验证器二维码。</p>
        <a-form layout="vertical" :model="setupPasswordForm" @finish="handleStartSetup">
          <a-form-item
            name="currentPassword"
            label="当前密码"
            :rules="[{ required: true, message: '请输入当前密码' }]">
            <a-input-password
              v-model:value="setupPasswordForm.currentPassword"
              autocomplete="current-password" />
          </a-form-item>
          <div class="modal-footer-actions">
            <a-button @click="closeSetupModal">取消</a-button>
            <a-button type="primary" html-type="submit" :loading="setupSubmitting">下一步</a-button>
          </div>
        </a-form>
      </template>

      <template v-else-if="setupStep === 'verify' && setupData">
        <p class="modal-tip">
          使用验证器应用扫描下方二维码，或手动录入密钥，随后输入生成的 6 位动态验证码完成绑定。
        </p>
        <div class="qrcode-box">
          <a-qrcode :value="setupData.otpauth_uri" :size="180" />
        </div>
        <div class="manual-key-box">
          <span class="manual-key-label">手动录入密钥</span>
          <a-typography-text code copyable>{{ setupData.manual_key }}</a-typography-text>
        </div>
        <a-form layout="vertical" :model="setupVerifyForm" @finish="handleEnableTwoFactor">
          <a-form-item
            name="code"
            label="6 位动态验证码"
            :rules="[{ required: true, whitespace: true, message: '请输入 6 位动态验证码' }]">
            <a-input
              v-model:value="setupVerifyForm.code"
              inputmode="numeric"
              autocomplete="one-time-code"
              :maxlength="6"
              placeholder="输入 6 位数字验证码" />
          </a-form-item>
          <div class="modal-footer-actions">
            <a-button @click="closeSetupModal">取消</a-button>
            <a-button type="primary" html-type="submit" :loading="setupSubmitting">
              确认开启
            </a-button>
          </div>
        </a-form>
      </template>

      <template v-else-if="setupStep === 'recovery'">
        <a-alert
          type="warning"
          show-icon
          message="请妥善保存以下一次性恢复码"
          description="当手机丢失或无法获取动态验证码时，可使用恢复码登录。此列表仅显示一次。" />
        <div class="recovery-grid">
          <code v-for="item in recoveryCodes" :key="item" class="recovery-item">{{ item }}</code>
        </div>
        <div class="modal-footer-actions">
          <a-space>
            <a-button @click="copyRecoveryCodes">复制全部</a-button>
            <a-button @click="downloadRecoveryCodes">下载保存</a-button>
          </a-space>
          <a-button type="primary" @click="finishRecoveryDisplay">我已保存，完成</a-button>
        </div>
      </template>
    </a-modal>

    <a-modal
      v-model:open="regenerateModalOpen"
      title="重新生成恢复码"
      width="460px"
      :mask-closable="false"
      :footer="null"
      @cancel="closeRegenerateModal">
      <template v-if="recoveryCodes.length === 0">
        <a-alert
          type="info"
          show-icon
          class="modal-alert"
          message="重新生成后，此前未使用的恢复码将立即失效。" />
        <a-form layout="vertical" :model="regenerateForm" @finish="handleRegenerateRecoveryCodes">
          <a-form-item
            name="currentPassword"
            label="当前密码"
            :rules="[{ required: true, message: '请输入当前密码' }]">
            <a-input-password
              v-model:value="regenerateForm.currentPassword"
              autocomplete="current-password" />
          </a-form-item>
          <a-form-item
            name="code"
            label="6 位动态验证码"
            :rules="[{ required: true, whitespace: true, message: '请输入 6 位动态验证码' }]">
            <a-input
              v-model:value="regenerateForm.code"
              inputmode="numeric"
              autocomplete="one-time-code"
              :maxlength="6"
              placeholder="输入 6 位数字验证码" />
          </a-form-item>
          <div class="modal-footer-actions">
            <a-button @click="closeRegenerateModal">取消</a-button>
            <a-button type="primary" html-type="submit" :loading="regenerateSubmitting">
              生成新恢复码
            </a-button>
          </div>
        </a-form>
      </template>
      <template v-else>
        <a-alert
          type="warning"
          show-icon
          message="请妥善保存新的恢复码"
          description="旧恢复码已全部作废，新恢复码仅显示这一次。" />
        <div class="recovery-grid">
          <code v-for="item in recoveryCodes" :key="item" class="recovery-item">{{ item }}</code>
        </div>
        <div class="modal-footer-actions">
          <a-space>
            <a-button @click="copyRecoveryCodes">复制全部</a-button>
            <a-button @click="downloadRecoveryCodes">下载保存</a-button>
          </a-space>
          <a-button type="primary" @click="closeRegenerateModal">我已保存，完成</a-button>
        </div>
      </template>
    </a-modal>

    <a-modal
      v-model:open="disableModalOpen"
      title="关闭双因素认证"
      width="460px"
      :mask-closable="false"
      :footer="null"
      @cancel="closeDisableModal">
      <a-alert
        type="warning"
        show-icon
        class="modal-alert"
        message="关闭后将降低账号防护等级，且当前会话会立即失效并需重新登录。" />
      <a-form layout="vertical" :model="disableForm" @finish="handleDisableTwoFactor">
        <a-form-item
          name="currentPassword"
          label="当前密码"
          :rules="[{ required: true, message: '请输入当前密码' }]">
          <a-input-password
            v-model:value="disableForm.currentPassword"
            autocomplete="current-password" />
        </a-form-item>
        <a-form-item name="method" label="验证方式">
          <a-radio-group v-model:value="disableForm.method">
            <a-radio-button value="totp">动态验证码</a-radio-button>
            <a-radio-button value="recovery">一次性恢复码</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item
          name="code"
          :label="disableForm.method === 'totp' ? '6 位动态验证码' : '一次性恢复码'"
          :rules="[{ required: true, whitespace: true, message: '请输入验证码' }]">
          <a-input
            v-model:value="disableForm.code"
            :inputmode="disableForm.method === 'totp' ? 'numeric' : 'text'"
            :maxlength="disableForm.method === 'totp' ? 6 : 16"
            :placeholder="
              disableForm.method === 'totp' ? '输入 6 位数字验证码' : '输入恢复码（如 ABCD-EFGH）'
            " />
        </a-form-item>
        <div class="modal-footer-actions">
          <a-button @click="closeDisableModal">取消</a-button>
          <a-button type="primary" danger html-type="submit" :loading="disableSubmitting">
            确认关闭
          </a-button>
        </div>
      </a-form>
    </a-modal>
  </PageLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { App } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  disableTwoFactor,
  enableTwoFactor,
  getTwoFactorStatus,
  regenerateTwoFactorRecoveryCodes,
  setupTwoFactor,
  updateCurrentUserPassword,
  type TwoFactorMethod,
  type TwoFactorSetupResult,
  type TwoFactorStatus,
} from '@/api/auth'
import PageLayout from '@/components/PageLayout/index.vue'
import { useUserStore } from '@/stores/user'
import { formatTimestamp } from '@/utils/datetime'

const router = useRouter()
const user = useUserStore()
const { message } = App.useApp()
const saving = ref(false)
const form = reactive({ currentPassword: '', newPassword: '' })

const twoFactorLoading = ref(false)
const twoFactorStatus = reactive<TwoFactorStatus>({
  enabled: Boolean(user.profile?.totp_enabled),
  enabled_at: null,
  recovery_codes_remaining: 0,
})

const setupModalOpen = ref(false)
const setupStep = ref<'password' | 'verify' | 'recovery'>('password')
const setupSubmitting = ref(false)
const setupData = ref<TwoFactorSetupResult | null>(null)
const setupPasswordForm = reactive({ currentPassword: '' })
const setupVerifyForm = reactive({ code: '' })
const recoveryCodes = ref<string[]>([])

const regenerateModalOpen = ref(false)
const regenerateSubmitting = ref(false)
const regenerateForm = reactive({ currentPassword: '', code: '' })

const disableModalOpen = ref(false)
const disableSubmitting = ref(false)
const disableForm = reactive({
  currentPassword: '',
  code: '',
  method: 'totp' as TwoFactorMethod,
})

async function fetchTwoFactorStatus() {
  twoFactorLoading.value = true
  try {
    const res = await getTwoFactorStatus()
    if (res.ok && res.data) {
      twoFactorStatus.enabled = res.data.enabled
      twoFactorStatus.enabled_at = res.data.enabled_at ?? null
      twoFactorStatus.recovery_codes_remaining = res.data.recovery_codes_remaining
      if (user.profile) {
        user.setProfile({ ...user.profile, totp_enabled: res.data.enabled })
      }
    }
  } finally {
    twoFactorLoading.value = false
  }
}

async function save() {
  if (saving.value) return
  saving.value = true
  try {
    const result = await updateCurrentUserPassword({
      current_password: form.currentPassword,
      new_password: form.newPassword,
    })
    if (!result.ok) {
      message.error(result.msg || '修改密码失败')
      return
    }
    user.clearSession()
    message.success('密码已修改，请重新登录')
    await router.replace('/login')
  } finally {
    saving.value = false
  }
}

function openSetupModal() {
  setupStep.value = 'password'
  setupData.value = null
  setupPasswordForm.currentPassword = ''
  setupVerifyForm.code = ''
  recoveryCodes.value = []
  setupModalOpen.value = true
}

function closeSetupModal() {
  setupModalOpen.value = false
  setupPasswordForm.currentPassword = ''
  setupVerifyForm.code = ''
  setupData.value = null
  recoveryCodes.value = []
}

async function handleStartSetup() {
  if (setupSubmitting.value) return
  setupSubmitting.value = true
  try {
    const res = await setupTwoFactor(setupPasswordForm.currentPassword)
    if (!res.ok || !res.data) {
      message.error(res.msg || '生成绑定信息失败')
      return
    }
    setupData.value = res.data
    setupPasswordForm.currentPassword = ''
    setupStep.value = 'verify'
  } finally {
    setupSubmitting.value = false
  }
}

async function handleEnableTwoFactor() {
  if (setupSubmitting.value) return
  setupSubmitting.value = true
  try {
    const res = await enableTwoFactor(setupVerifyForm.code.trim())
    if (!res.ok || !res.data) {
      message.error(res.msg || '开启双因素认证失败')
      return
    }
    recoveryCodes.value = res.data.recovery_codes
    setupVerifyForm.code = ''
    setupStep.value = 'recovery'
    message.success('双因素认证已开启')
    await fetchTwoFactorStatus()
  } finally {
    setupSubmitting.value = false
  }
}

function finishRecoveryDisplay() {
  closeSetupModal()
}

function openRegenerateModal() {
  regenerateForm.currentPassword = ''
  regenerateForm.code = ''
  recoveryCodes.value = []
  regenerateModalOpen.value = true
}

function closeRegenerateModal() {
  regenerateModalOpen.value = false
  regenerateForm.currentPassword = ''
  regenerateForm.code = ''
  recoveryCodes.value = []
}

async function handleRegenerateRecoveryCodes() {
  if (regenerateSubmitting.value) return
  regenerateSubmitting.value = true
  try {
    const res = await regenerateTwoFactorRecoveryCodes({
      current_password: regenerateForm.currentPassword,
      code: regenerateForm.code.trim(),
    })
    if (!res.ok || !res.data) {
      message.error(res.msg || '重新生成恢复码失败')
      return
    }
    recoveryCodes.value = res.data.recovery_codes
    regenerateForm.currentPassword = ''
    regenerateForm.code = ''
    message.success('已生成新的恢复码')
    await fetchTwoFactorStatus()
  } finally {
    regenerateSubmitting.value = false
  }
}

function openDisableModal() {
  disableForm.currentPassword = ''
  disableForm.code = ''
  disableForm.method = 'totp'
  disableModalOpen.value = true
}

function closeDisableModal() {
  disableModalOpen.value = false
  disableForm.currentPassword = ''
  disableForm.code = ''
}

async function handleDisableTwoFactor() {
  if (disableSubmitting.value) return
  disableSubmitting.value = true
  try {
    const res = await disableTwoFactor({
      current_password: disableForm.currentPassword,
      code: disableForm.code.trim(),
      method: disableForm.method,
    })
    if (!res.ok) {
      message.error(res.msg || '关闭双因素认证失败')
      return
    }
    closeDisableModal()
    user.clearSession()
    message.success('双因素认证已关闭，请重新登录')
    await router.replace('/login')
  } finally {
    disableSubmitting.value = false
  }
}

async function copyRecoveryCodes() {
  if (recoveryCodes.value.length === 0) return
  try {
    await navigator.clipboard.writeText(recoveryCodes.value.join('\n'))
    message.success('恢复码已复制到剪贴板')
  } catch {
    message.error('复制失败，请手动选中保存')
  }
}

function downloadRecoveryCodes() {
  if (recoveryCodes.value.length === 0) return
  const username = user.profile?.username || 'account'
  const content = [
    `Mori Admin 双因素认证恢复码 (${username})`,
    '每组恢复码仅可使用一次，请妥善离线保存：',
    '',
    ...recoveryCodes.value,
    '',
  ].join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `mori-admin-2fa-recovery-${username}.txt`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  fetchTwoFactorStatus()
})
</script>

<style lang="scss" scoped>
.security-sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-desc {
  margin: 0 0 16px;
  line-height: 1.6;
  color: var(--ant-color-text-secondary);
}

.status-descriptions {
  margin-bottom: 16px;
}

.low-code-tip {
  margin-left: 6px;
  color: var(--ant-color-warning);
}

.status-actions {
  display: flex;
}

.modal-tip {
  margin: 0 0 16px;
  line-height: 1.6;
  color: var(--ant-color-text-secondary);
}

.modal-alert {
  margin-bottom: 16px;
}

.qrcode-box {
  display: flex;
  justify-content: center;
  padding: 12px;
  margin-bottom: 12px;
  background: var(--ant-color-bg-layout);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 8px;
}

.manual-key-box {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 16px;
  background: var(--ant-color-bg-layout);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 8px;
}

.manual-key-label {
  font-size: 13px;
  color: var(--ant-color-text-secondary);
}

.recovery-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 16px 0;
}

.recovery-item {
  padding: 8px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 14px;
  font-weight: 600;
  color: var(--ant-color-text);
  text-align: center;
  letter-spacing: 0.06em;
  background: var(--ant-color-bg-layout);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 6px;
}

.modal-footer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
