<template>
  <PageLayout title="品牌设置" max-width="42rem">
    <a-card title="系统 Logo">
      <a-spin :spinning="loading">
        <a-form layout="vertical" :model="form" @finish="save">
          <a-form-item
            name="file"
            label="Logo 图片"
            html-for="logo-file"
            extra="支持 PNG、JPEG 或 WebP，最大 1 MB。">
            <a-upload
              id="logo-file"
              name="logo"
              list-type="picture-card"
              accept="image/png,image/jpeg,image/webp"
              :before-upload="selectFile"
              :disabled="loading || saving"
              :file-list="[]"
              :show-upload-list="false">
              <img
                v-if="preview || settings.logo"
                :src="preview || settings.logo"
                class="logo-image"
                alt="更换 Logo" />
              <a-space v-else direction="vertical" :size="4">
                <PlusOutlined aria-hidden="true" />
                <span>选择 Logo</span>
              </a-space>
            </a-upload>
            <a-alert v-if="fileError" type="error" :message="fileError" show-icon role="alert" />
          </a-form-item>
          <a-space wrap>
            <a-button type="primary" html-type="submit" :loading="saving" :disabled="!form.file">
              保存 Logo
            </a-button>
            <a-button
              v-if="isCustomLogo && !form.file"
              html-type="button"
              :disabled="loading || saving"
              @click="restoreDefault">
              恢复默认
            </a-button>
          </a-space>
        </a-form>
      </a-spin>
    </a-card>
  </PageLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { App, type UploadProps } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { resetLogo, updateLogo } from '@/api/branding'
import PageLayout from '@/components/PageLayout/index.vue'
import defaultSettings from '@/setting'
import { useSettingsStore } from '@/stores/setting'

const settings = useSettingsStore()
const isCustomLogo = computed(
  () => Boolean(settings.logo) && settings.logo !== defaultSettings.logo
)
const { message } = App.useApp()
const loading = ref(true)
const saving = ref(false)
const form = reactive<{ file?: File }>({})
const fileError = ref('')
const preview = ref('')

watch(
  () => form.file,
  (selected, _previous, onCleanup) => {
    preview.value = selected ? URL.createObjectURL(selected) : ''
    if (selected) {
      const objectUrl = preview.value
      onCleanup(() => URL.revokeObjectURL(objectUrl))
    }
  }
)

onMounted(async () => {
  const result = await settings.refreshLogo()
  if (!result.ok) message.error(result.msg || '读取 Logo 失败')
  loading.value = false
})

const selectFile: UploadProps['beforeUpload'] = (selected) => {
  fileError.value = ''
  form.file = undefined
  if (
    !['image/png', 'image/jpeg', 'image/webp'].includes(selected.type) ||
    !selected.size ||
    selected.size > 1024 * 1024
  ) {
    fileError.value = '请选择不超过 1 MB 的 PNG、JPEG 或 WebP 图片'
    return false
  }
  form.file = selected
  return false
}

async function save() {
  if (!form.file || saving.value) return
  saving.value = true
  try {
    const result = await updateLogo(form.file)
    if (!result.ok || !result.data) {
      message.error(result.msg || '保存 Logo 失败')
      return
    }
    settings.applyLogo(result.data.logo)
    form.file = undefined
    message.success('Logo 已更新')
  } finally {
    saving.value = false
  }
}

async function restoreDefault() {
  if (saving.value) return
  saving.value = true
  try {
    const result = await resetLogo()
    if (!result.ok || !result.data) {
      message.error(result.msg || '恢复默认 Logo 失败')
      return
    }
    settings.applyLogo(null)
    message.success('已恢复默认外观')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.logo-image {
  width: 100%;
  height: 100%;
  padding: 4px;
  object-fit: contain;
  background: var(--ant-color-text-light-solid);
  border-radius: 6px;
}
</style>
