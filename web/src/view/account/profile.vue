<template>
  <PageLayout title="个人资料" description="更新显示名称与联系邮箱。" max-width="42rem">
    <a-card>
      <a-form layout="vertical" :model="form" @finish="save">
        <a-form-item label="用户名">
          <a-input :value="user.profile?.username" disabled />
        </a-form-item>
        <a-form-item
          name="displayName"
          label="显示名称"
          :rules="[{ required: true, whitespace: true, message: '请输入显示名称' }]">
          <a-input v-model:value="form.displayName" :maxlength="128" />
        </a-form-item>
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="form.email" type="email" autocomplete="email" />
        </a-form-item>
        <a-button type="primary" html-type="submit" :loading="saving">保存资料</a-button>
      </a-form>
    </a-card>
  </PageLayout>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { App } from 'ant-design-vue'
import { updateCurrentUserProfile } from '@/api/auth'
import PageLayout from '@/components/PageLayout/index.vue'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const { message } = App.useApp()
const saving = ref(false)
const form = reactive({ displayName: '', email: '' })

watch(
  () => user.profile,
  (profile) => {
    form.displayName = profile?.display_name ?? ''
    form.email = profile?.email ?? ''
  },
  { immediate: true }
)

async function save() {
  if (saving.value) return
  saving.value = true
  try {
    const result = await updateCurrentUserProfile({
      display_name: form.displayName.trim(),
      email: form.email.trim() || null,
    })
    if (!result.ok || !result.data) {
      message.error(result.msg || '保存失败')
      return
    }
    user.setProfile(result.data)
    message.success('已保存')
  } finally {
    saving.value = false
  }
}
</script>
