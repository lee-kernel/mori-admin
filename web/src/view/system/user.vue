<template>
  <PageLayout scroll="region" description="查找用户并维护账号资料与所属用户组。">
    <template #actions>
      <a-button v-if="canManage('create')" type="primary" @click="openCreateDialog">
        <template #icon><PlusOutlined /></template>
        新增用户
      </a-button>
    </template>
    <template #filter>
      <PageFilterBar>
        <template #basic>
          <a-input-search
            v-model:value="queryForm.keyword"
            placeholder="用户名、姓名或邮箱"
            allow-clear
            enter-button="搜索"
            @search="handleSearch" />
        </template>
        <template #submit>
          <a-button @click="handleReset">重置</a-button>
        </template>
      </PageFilterBar>
    </template>
    <div class="user-page">
      <a-alert v-if="loadError" type="error" show-icon :message="loadError" class="page-error">
        <template #action><a-button size="small" @click="fetchUsers">重试</a-button></template>
      </a-alert>

      <TableSection>
        <a-table
          :columns="columns"
          :data-source="tableData"
          :loading="loading"
          :pagination="false"
          :scroll="{ x: '100%', y: '100%' }"
          row-key="id"
          size="middle">
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.key === 'index'">
              {{ (queryForm.pageNum - 1) * queryForm.pageSize + index + 1 }}
            </template>
            <template v-else-if="column.key === 'email'">
              {{ record.email || '-' }}
            </template>
            <template v-else-if="column.key === 'is_active'">
              <a-tag :color="record.is_active ? 'success' : 'default'">
                {{ record.is_active ? '启用' : '禁用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'totp_enabled'">
              <a-tag :color="record.totp_enabled ? 'processing' : 'default'">
                {{ record.totp_enabled ? '已开启' : '未开启' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'group_name'">
              {{ record.group_name || '-' }}
            </template>
            <template v-else-if="column.key === 'actions'">
              <div class="app-table-actions">
                <a-button
                  v-if="canManage('edit')"
                  type="link"
                  size="small"
                  @click="openEditDialog(record)">
                  <template #icon><EditOutlined /></template>
                  修改
                </a-button>
                <a-button
                  v-if="canManage('edit')"
                  type="link"
                  size="small"
                  class="warning-link"
                  :disabled="record.username === 'admin'"
                  @click="openPasswordDialog(record)">
                  <template #icon><KeyOutlined /></template>
                  改密码
                </a-button>
                <a-button
                  v-if="canManage('edit')"
                  type="link"
                  size="small"
                  class="warning-link"
                  :disabled="record.username === 'admin' || !record.totp_enabled"
                  @click="handleResetTwoFactor(record)">
                  <template #icon><SafetyOutlined /></template>
                  重置 2FA
                </a-button>
                <a-button
                  v-if="canManage('delete')"
                  type="link"
                  size="small"
                  danger
                  :disabled="record.username === 'admin'"
                  @click="handleDelete(record)">
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </div>
            </template>
          </template>
        </a-table>

        <template #footer>
          <a-pagination
            v-model:current="queryForm.pageNum"
            v-model:page-size="queryForm.pageSize"
            show-size-changer
            show-quick-jumper
            :page-size-options="['10', '20', '50', '100']"
            :total="total"
            :show-total="(totalCount) => `共 ${totalCount} 条`"
            @change="fetchUsers"
            @show-size-change="fetchUsers" />
        </template>
      </TableSection>
      <a-modal
        v-model:open="userDialogVisible"
        :title="userDialogTitle"
        width="520px"
        :confirm-loading="submitLoading"
        ok-text="保存"
        cancel-text="取消"
        @ok="submitUserForm">
        <a-form
          ref="userFormRef"
          :model="userForm"
          :rules="userRules"
          :label-col="{ style: { width: '92px' } }"
          class="dialog-form">
          <a-form-item label="用户名" name="username">
            <a-input
              v-model:value="userForm.username"
              :disabled="dialogMode === 'edit'"
              placeholder="请输入用户名" />
          </a-form-item>
          <a-form-item label="显示名称" name="display_name">
            <a-input v-model:value="userForm.display_name" placeholder="请输入显示名称" />
          </a-form-item>
          <a-form-item label="邮箱" name="email">
            <a-input v-model:value="userForm.email" placeholder="请输入邮箱" allow-clear />
          </a-form-item>
          <a-form-item label="用户组" name="group_id">
            <a-select
              v-model:value="userForm.group_id"
              placeholder="请选择用户组"
              :options="groupOptions" />
          </a-form-item>
          <a-form-item v-if="dialogMode === 'create'" label="密码" name="password">
            <a-input-password v-model:value="userForm.password" placeholder="请输入密码" />
          </a-form-item>
          <a-form-item label="状态" name="is_active">
            <a-switch
              v-model:checked="userForm.is_active"
              checked-children="启用"
              un-checked-children="禁用" />
          </a-form-item>
        </a-form>
      </a-modal>

      <a-modal
        v-model:open="passwordDialogVisible"
        title="修改密码"
        width="460px"
        :confirm-loading="submitLoading"
        ok-text="保存"
        cancel-text="取消"
        @ok="submitPasswordForm">
        <a-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          :label-col="{ style: { width: '92px' } }"
          class="dialog-form">
          <a-form-item label="用户">
            <a-input :value="currentUser?.username" disabled />
          </a-form-item>
          <a-form-item label="新密码" name="password">
            <a-input-password v-model:value="passwordForm.password" placeholder="请输入新密码" />
          </a-form-item>
          <a-form-item label="确认密码" name="confirmPassword">
            <a-input-password
              v-model:value="passwordForm.confirmPassword"
              placeholder="请再次输入新密码" />
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { App, type TableColumnsType } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import {
  DeleteOutlined,
  EditOutlined,
  KeyOutlined,
  PlusOutlined,
  SafetyOutlined,
} from '@ant-design/icons-vue'
import PageLayout from '@/components/PageLayout/index.vue'
import PageFilterBar from '@/components/PageFilterBar/index.vue'
import TableSection from '@/components/TableSection/index.vue'
import { getGroupOptions, type GroupItem } from '@/api/group'
import {
  createUser,
  deleteUser,
  getUserPage,
  resetUserTwoFactor,
  updateUser,
  updateUserPassword,
  type UserItem,
} from '@/api/user'
import { useUserStore } from '@/stores/user'

const { message, modal: Modal } = App.useApp()

const userStore = useUserStore()

function canManage(operation: 'create' | 'edit' | 'delete') {
  return (
    userStore.profile?.is_admin &&
    userStore.profile.operation_permission_keys?.includes(`user.${operation}`)
  )
}
const loading = ref(false)
const loadError = ref('')
const submitLoading = ref(false)
const tableData = ref<UserItem[]>([])
const total = ref(0)
const groups = ref<GroupItem[]>([])
const columns: TableColumnsType = [
  { title: '#', key: 'index', width: 64, fixed: 'left' },
  { title: '用户名', dataIndex: 'username', key: 'username', width: 150, ellipsis: true },
  {
    title: '显示名称',
    dataIndex: 'display_name',
    key: 'display_name',
    width: 160,
    ellipsis: true,
  },
  { title: '邮箱', dataIndex: 'email', key: 'email', width: 220, ellipsis: true },
  { title: '用户组', dataIndex: 'group_name', key: 'group_name', width: 140, ellipsis: true },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 100 },
  { title: '2FA', dataIndex: 'totp_enabled', key: 'totp_enabled', width: 96 },
  { title: '操作', key: 'actions', width: 320, fixed: 'right' },
]

const queryForm = reactive({
  pageNum: 1,
  pageSize: 10,
  keyword: '',
})

const userDialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentUser = ref<UserItem | null>(null)
const userFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

const userForm = reactive({
  username: '',
  display_name: '',
  email: '',
  password: '',
  is_active: true,
  group_id: undefined as number | undefined,
})

const passwordForm = reactive({
  password: '',
  confirmPassword: '',
})

const userDialogTitle = computed(() => (dialogMode.value === 'create' ? '新增用户' : '修改用户'))
const groupOptions = computed(() =>
  groups.value.map((group) => ({ label: group.name, value: group.id }))
)
const userRules: Record<string, Rule[]> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }],
  group_id: [{ required: true, message: '请选择用户组', trigger: 'change' }],
  password: [{ required: true, min: 6, message: '请输入至少 6 位密码', trigger: 'blur' }],
}

const passwordRules: Record<string, Rule[]> = {
  password: [
    {
      required: true,
      min: 6,
      message: '请输入至少 6 位新密码',
      trigger: 'blur',
    },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: async (_rule, value) => {
        if (value !== passwordForm.password) {
          return Promise.reject(new Error('两次输入的密码不一致'))
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
}

async function fetchGroups() {
  const res = await getGroupOptions()
  if (res.ok && res.data) {
    groups.value = res.data.groups
    if (!userForm.group_id) {
      userForm.group_id = groups.value[0]?.id
    }
  }
}

async function fetchUsers() {
  loading.value = true
  loadError.value = ''
  const res = await getUserPage({
    pageNum: queryForm.pageNum,
    pageSize: queryForm.pageSize,
    keyword: queryForm.keyword.trim() || undefined,
  })
  loading.value = false

  if (!res.ok || !res.data) {
    loadError.value = res.msg || '获取用户列表失败'
    return
  }

  tableData.value = res.data.list
  total.value = res.data.total
}

function handleSearch() {
  queryForm.pageNum = 1
  fetchUsers()
}

function handleReset() {
  queryForm.keyword = ''
  queryForm.pageNum = 1
  fetchUsers()
}

function resetUserForm() {
  userForm.username = ''
  userForm.display_name = ''
  userForm.email = ''
  userForm.password = ''
  userForm.is_active = true
  userForm.group_id = groups.value[0]?.id
  userFormRef.value?.clearValidate()
}

function openCreateDialog() {
  dialogMode.value = 'create'
  currentUser.value = null
  resetUserForm()
  userDialogVisible.value = true
}

function openEditDialog(row: UserItem) {
  dialogMode.value = 'edit'
  currentUser.value = row
  userForm.username = row.username
  userForm.display_name = row.display_name
  userForm.email = row.email || ''
  userForm.password = ''
  userForm.is_active = row.is_active
  userForm.group_id = row.group_id || undefined
  userFormRef.value?.clearValidate()
  userDialogVisible.value = true
}

async function submitUserForm() {
  const validation = await userFormRef.value?.validate().catch(() => false)
  if (!validation) return

  submitLoading.value = true
  const res =
    dialogMode.value === 'create'
      ? await createUser({
          username: userForm.username.trim(),
          display_name: userForm.display_name.trim(),
          email: userForm.email.trim() || null,
          password: userForm.password,
          is_active: userForm.is_active,
          group_id: userForm.group_id,
        })
      : await updateUser(currentUser.value!.id, {
          display_name: userForm.display_name.trim(),
          email: userForm.email.trim() || null,
          is_active: userForm.is_active,
          group_id: userForm.group_id,
        })
  submitLoading.value = false

  if (!res.ok) {
    message.error(res.msg || '保存失败')
    return
  }

  message.success('保存成功')
  userDialogVisible.value = false
  if (res.data?.id === userStore.profile?.id) {
    userStore.setProfile(res.data)
  }
  fetchUsers()
}

function openPasswordDialog(row: UserItem) {
  currentUser.value = row
  passwordForm.password = ''
  passwordForm.confirmPassword = ''
  passwordFormRef.value?.clearValidate()
  passwordDialogVisible.value = true
}

async function submitPasswordForm() {
  const validation = await passwordFormRef.value?.validate().catch(() => false)
  if (!validation || !currentUser.value) return

  submitLoading.value = true
  const res = await updateUserPassword(currentUser.value.id, {
    password: passwordForm.password,
  })
  submitLoading.value = false

  if (!res.ok) {
    message.error(res.msg || '修改密码失败')
    return
  }

  message.success('密码已修改')
  passwordDialogVisible.value = false
}

function handleResetTwoFactor(row: UserItem) {
  Modal.confirm({
    title: '重置双因素认证',
    content: `确认重置用户「${row.username}」的双因素认证？重置后该用户当前会话会失效，下次登录无需输入动态验证码。`,
    okText: '确认重置',
    cancelText: '取消',
    okButtonProps: { danger: true },
    async onOk() {
      const res = await resetUserTwoFactor(row.id)
      if (!res.ok) {
        message.error(res.msg || '重置 2FA 失败')
        return Promise.reject()
      }
      message.success('已重置该用户的双因素认证')
      await fetchUsers()
      return Promise.resolve()
    },
  })
}

function handleDelete(row: UserItem) {
  Modal.confirm({
    title: '删除用户',
    content: `确认删除用户「${row.username}」？其全部私有数据将永久删除，公开脚本及分类转交默认管理员，审计日志保留，文件将在后台清理。此操作不可撤销。`,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { danger: true },
    async onOk() {
      const res = await deleteUser(row.id)
      if (!res.ok) {
        message.error(res.msg || '删除失败')
        return Promise.reject()
      }

      message.success('删除成功')
      if (tableData.value.length === 1 && queryForm.pageNum > 1) {
        queryForm.pageNum -= 1
      }
      await fetchUsers()
      return Promise.resolve()
    },
  })
}

onMounted(async () => {
  await fetchGroups()
  await fetchUsers()
})
</script>

<style lang="scss" scoped>
.user-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  min-height: 0;
}

.warning-link {
  color: var(--ant-color-warning);

  &:hover {
    color: var(--ant-color-warning);
  }
}

.dialog-form {
  padding-top: 12px;
}
</style>
