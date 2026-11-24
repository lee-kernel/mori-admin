<template>
  <PageLayout scroll="region" description="管理用户组及其操作权限。">
    <template #actions>
      <a-button
        v-if="canManage('create')"
        type="primary"
        :disabled="!operationPermissions.length"
        @click="openCreateDialog">
        <template #icon><PlusOutlined /></template>
        新增用户组
      </a-button>
    </template>
    <template #filter>
      <PageFilterBar>
        <template #basic>
          <a-input-search
            v-model:value="queryForm.keyword"
            placeholder="用户组名称或说明"
            allow-clear
            enter-button="搜索"
            @search="handleSearch" />
        </template>
        <template #submit>
          <a-button @click="handleReset">重置</a-button>
        </template>
      </PageFilterBar>
    </template>
    <div class="group-page">
      <a-alert v-if="loadError" type="error" show-icon :message="loadError" class="page-error">
        <template #action><a-button size="small" @click="fetchGroups">重试</a-button></template>
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
            <template v-else-if="column.key === 'description'">
              {{ record.description || '-' }}
            </template>
            <template v-else-if="column.key === 'menu_ids'">
              <a-tag>{{ record.menu_ids.length }} 个菜单</a-tag>
            </template>
            <template v-else-if="column.key === 'permission_keys'">
              <a-tag>{{ record.permission_keys.length }} 项操作</a-tag>
            </template>
            <template v-else-if="column.key === 'is_system'">
              <a-tag :color="record.is_system ? 'blue' : 'default'">
                {{ record.is_system ? '系统内置' : '自定义' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'is_admin'">
              <a-tag :color="record.is_admin ? 'red' : 'default'">
                {{ record.is_admin ? '管理员组' : '普通组' }}
              </a-tag>
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
                  v-if="canManage('delete')"
                  type="link"
                  size="small"
                  danger
                  :disabled="record.is_system"
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
            @change="fetchGroups"
            @show-size-change="fetchGroups" />
        </template>
      </TableSection>

      <a-modal
        :open="dialogVisible"
        :title="dialogTitle"
        width="min(960px, calc(100vw - 32px))"
        :body-style="{ maxHeight: 'min(72vh, 760px)', overflowY: 'auto' }"
        @cancel="handleDialogCancel">
        <template #footer>
          <a-button @click="handleDialogCancel">{{ isAdminGroup ? '关闭' : '取消' }}</a-button>
          <a-button
            v-if="!isAdminGroup"
            type="primary"
            :loading="submitLoading"
            @click="submitForm">
            保存
          </a-button>
        </template>
        <a-form
          ref="formRef"
          :model="form"
          :rules="rules"
          :label-col="{ style: { width: '78px', textAlign: 'right' } }"
          :wrapper-col="{ style: { minWidth: 0 } }"
          class="dialog-form">
          <a-form-item label="名称" name="name">
            <a-input
              v-model:value="form.name"
              :disabled="isAdminGroup"
              placeholder="请输入用户组名称" />
          </a-form-item>
          <a-form-item label="说明" name="description">
            <a-textarea
              v-model:value="form.description"
              :disabled="isAdminGroup"
              placeholder="请输入用户组说明"
              :rows="2" />
          </a-form-item>
          <a-alert
            v-if="isAdminGroup"
            class="admin-group-alert"
            message="管理员组默认拥有全部菜单和操作权限，不可修改。"
            type="info"
            show-icon />
          <a-alert
            v-else-if="selectedHighRisk.length"
            class="risk-alert"
            type="warning"
            show-icon
            :message="`已选择 ${selectedHighRisk.length} 项高风险权限，保存前请核对。`" />
          <a-form-item label="菜单" name="menu_ids">
            <div class="menu-tree-wrapper">
              <div class="menu-tree-toolbar">
                <a-input-search
                  v-model:value="menuSearch"
                  placeholder="搜索菜单"
                  allow-clear
                  size="small"
                  class="menu-tree-search" />
                <a-space size="small">
                  <a-button size="small" @click="handleExpandAll">展开</a-button>
                  <a-button size="small" @click="handleCollapseAll">折叠</a-button>
                  <a-button v-if="!isAdminGroup" size="small" @click="handleCheckAll">
                    全选
                  </a-button>
                  <a-button v-if="!isAdminGroup" size="small" type="text" @click="handleUncheckAll">
                    清空
                  </a-button>
                </a-space>
              </div>
              <div class="menu-tree-box">
                <a-empty
                  v-if="menuSearch && !menuMatches.length"
                  description="没有找到匹配的菜单" />
                <a-tree
                  v-else
                  v-model:checked-keys="form.menu_ids"
                  v-model:expanded-keys="menuExpandedKeys"
                  :tree-data="menuTree"
                  :field-names="{
                    children: 'children',
                    title: 'name',
                    key: 'id',
                  }"
                  :auto-expand-parent="menuAutoExpandParent"
                  checkable
                  :disabled="isAdminGroup"
                  block-node
                  class="menu-tree"
                  @expand="handleMenuExpand">
                  <template #title="node">
                    <span :class="{ 'menu-tree-hit': isMenuHit(node) }">
                      {{ node.name }}
                    </span>
                  </template>
                </a-tree>
              </div>
              <div class="menu-tree-count">
                已选 {{ form.menu_ids.length }} / {{ flatMenus.length }} 项
              </div>
            </div>
          </a-form-item>
          <a-form-item label="操作权限" name="permission_keys">
            <div class="permission-area">
              <div v-if="!isAdminGroup" class="permission-toolbar">
                <span>菜单控制导航，操作权限决定可调用的接口。</span>
                <a-button size="small" @click="applyReadOnlyPreset">仅保留查看</a-button>
              </div>
              <a-alert
                v-if="!isAdminGroup && writeWithoutRead.length"
                class="permission-hint"
                type="info"
                show-icon
                :message="`${writeWithoutRead.join('、')}已选写入或运行，但未选查看；相关列表可能不可见。`" />
              <OperationPermissionMatrix
                v-model="form.permission_keys"
                :items="operationPermissions"
                :readonly="isAdminGroup" />
              <div class="permission-count">
                已选 {{ form.permission_keys.length }} / {{ operationPermissions.length }} 项
              </div>
            </div>
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { App, type TableColumnsType } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons-vue'
import {
  createGroup,
  deleteGroup,
  getGroupPage,
  getOperationPermissions,
  updateGroup,
  type GroupItem,
  type OperationPermission,
} from '@/api/group'
import PageLayout from '@/components/PageLayout/index.vue'
import PageFilterBar from '@/components/PageFilterBar/index.vue'
import TableSection from '@/components/TableSection/index.vue'
import OperationPermissionMatrix from '@/components/OperationPermissionMatrix.vue'
import { getMenuTree, type MenuNode } from '@/api/menu'
import { useUserStore } from '@/stores/user'
import { syncDynamicRoutes } from '@/router'

const { message, modal: Modal } = App.useApp()

const userStore = useUserStore()

function canManage(operation: 'create' | 'edit' | 'delete') {
  return (
    userStore.profile?.is_admin &&
    userStore.profile.operation_permission_keys?.includes(`group.${operation}`)
  )
}
const loading = ref(false)
const loadError = ref('')
const submitLoading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentGroup = ref<GroupItem | null>(null)
const tableData = ref<GroupItem[]>([])
const menuTree = ref<MenuNode[]>([])
const operationPermissions = ref<OperationPermission[]>([])
const isAdminGroup = computed(() => Boolean(currentGroup.value?.is_admin))
const permissionGroups = computed(() => {
  const groups = new Map<string, OperationPermission[]>()
  for (const item of operationPermissions.value) {
    if (!groups.has(item.domain)) groups.set(item.domain, [])
    groups.get(item.domain)!.push(item)
  }
  return Array.from(groups, ([domain, items]) => ({ domain, label: items[0].domain_label, items }))
})
const selectedHighRisk = computed(() =>
  operationPermissions.value.filter(
    (item) => item.high_risk && form.permission_keys.includes(item.key)
  )
)
const writeWithoutRead = computed(() =>
  permissionGroups.value
    .filter((group) => {
      const read = group.items.find((item) => item.operation === 'read')
      return (
        read &&
        !form.permission_keys.includes(read.key) &&
        group.items.some(
          (item) => item.operation !== 'read' && form.permission_keys.includes(item.key)
        )
      )
    })
    .map((group) => group.label)
)
const menuSearch = ref('')
const menuExpandedKeys = ref<number[]>([])
const menuAutoExpandParent = ref(true)
const total = ref(0)
const formRef = ref<FormInstance>()
const initialSnapshot = ref('')

const queryForm = reactive({
  pageNum: 1,
  pageSize: 10,
  keyword: '',
})
const form = reactive({
  name: '',
  description: '',
  menu_ids: [] as number[],
  permission_keys: [] as string[],
})
const formSnapshot = () =>
  JSON.stringify({
    name: form.name.trim(),
    description: form.description.trim(),
    menu_ids: [...form.menu_ids].sort((a, b) => a - b),
    permission_keys: [...form.permission_keys].sort(),
  })
const hasUnsavedChanges = computed(() => formSnapshot() !== initialSnapshot.value)

const columns: TableColumnsType = [
  { title: '#', key: 'index', width: 64, fixed: 'left' },
  { title: '名称', dataIndex: 'name', key: 'name', width: 160, ellipsis: true },
  { title: '说明', dataIndex: 'description', key: 'description', width: 260, ellipsis: true },
  { title: '可访问菜单', dataIndex: 'menu_ids', key: 'menu_ids', width: 140 },
  { title: '操作权限', dataIndex: 'permission_keys', key: 'permission_keys', width: 130 },
  { title: '类型', dataIndex: 'is_system', key: 'is_system', width: 120 },
  { title: '权限级别', dataIndex: 'is_admin', key: 'is_admin', width: 120 },
  { title: '操作', key: 'actions', width: 180, fixed: 'right' },
]

const dialogTitle = computed(() => (dialogMode.value === 'create' ? '新增用户组' : '修改用户组'))
const rules: Record<string, Rule[]> = {
  name: [{ required: true, message: '请输入用户组名称', trigger: 'blur' }],
  menu_ids: [
    {
      type: 'array',
      required: true,
      min: 1,
      message: '请至少选择一个菜单',
      trigger: 'change',
    },
  ],
  permission_keys: [
    { type: 'array', required: true, min: 1, message: '请至少选择一项操作权限', trigger: 'change' },
  ],
}

async function fetchMenuTree() {
  const res = await getMenuTree()
  if (res.ok && res.data) {
    menuTree.value = res.data.list
    // 默认展开顶层节点
    menuExpandedKeys.value = res.data.list.map((m) => m.id)
  }
}

async function fetchOperationPermissions() {
  const res = await getOperationPermissions()
  if (res.ok && res.data) operationPermissions.value = res.data
  else message.error(res.msg || '获取操作权限失败，请刷新页面重试')
}

const flatMenus = computed<MenuNode[]>(() => {
  const list: MenuNode[] = []
  const walk = (nodes: MenuNode[]) => {
    nodes.forEach((node) => {
      list.push(node)
      if (node.children?.length) walk(node.children)
    })
  }
  walk(menuTree.value)
  return list
})
const menuMatches = computed(() => flatMenus.value.filter(isMenuHit))

function applyReadOnlyPreset() {
  form.permission_keys = form.permission_keys.filter((key) =>
    operationPermissions.value.some((item) => item.key === key && item.operation === 'read')
  )
}

function isMenuHit(node: MenuNode) {
  const keyword = menuSearch.value.trim().toLowerCase()
  if (!keyword) return false
  return node.name.toLowerCase().includes(keyword)
}

function handleMenuExpand(keys: (string | number)[]) {
  menuExpandedKeys.value = keys.map((k) => Number(k))
  menuAutoExpandParent.value = false
}

function handleExpandAll() {
  menuExpandedKeys.value = flatMenus.value.filter((m) => m.children?.length).map((m) => m.id)
}

function handleCollapseAll() {
  menuExpandedKeys.value = []
}

function handleCheckAll() {
  form.menu_ids = flatMenus.value.map((m) => m.id)
}

function handleUncheckAll() {
  Modal.confirm({
    title: '清空菜单选择？',
    content: '清空后需重新选择至少一个菜单才能保存。',
    okText: '清空',
    okButtonProps: { danger: true },
    onOk: () => {
      form.menu_ids = []
    },
  })
}

watch(menuSearch, (keyword) => {
  if (!keyword.trim()) {
    menuAutoExpandParent.value = false
    return
  }
  const parentMap = new Map<number, number | null>()
  const hits = new Set<number>()
  flatMenus.value.forEach((node) => {
    parentMap.set(node.id, node.parent_id ?? null)
    if (isMenuHit(node)) hits.add(node.id)
  })
  const expand = new Set<number>()
  hits.forEach((id) => {
    let cur = parentMap.get(id) ?? null
    while (cur != null) {
      expand.add(cur)
      cur = parentMap.get(cur) ?? null
    }
  })
  menuExpandedKeys.value = Array.from(expand)
  menuAutoExpandParent.value = true
})

async function fetchGroups() {
  loading.value = true
  loadError.value = ''
  const res = await getGroupPage({
    pageNum: queryForm.pageNum,
    pageSize: queryForm.pageSize,
    keyword: queryForm.keyword.trim() || undefined,
  })
  loading.value = false

  if (!res.ok || !res.data) {
    loadError.value = res.msg || '获取用户组列表失败'
    return
  }

  tableData.value = res.data.list
  total.value = res.data.total
}

function handleSearch() {
  queryForm.pageNum = 1
  fetchGroups()
}

function handleReset() {
  queryForm.keyword = ''
  queryForm.pageNum = 1
  fetchGroups()
}

function resetForm() {
  form.name = ''
  form.description = ''
  form.menu_ids = []
  form.permission_keys = []
  menuSearch.value = ''
  formRef.value?.clearValidate()
}

function openCreateDialog() {
  dialogMode.value = 'create'
  currentGroup.value = null
  resetForm()
  initialSnapshot.value = formSnapshot()
  dialogVisible.value = true
}

function openEditDialog(row: GroupItem) {
  dialogMode.value = 'edit'
  currentGroup.value = row
  form.name = row.name
  form.description = row.description || ''
  form.menu_ids = row.is_admin ? flatMenus.value.map((item) => item.id) : [...row.menu_ids]
  form.permission_keys = row.is_admin
    ? operationPermissions.value.map((item) => item.key)
    : [...row.permission_keys]
  menuSearch.value = ''
  formRef.value?.clearValidate()
  initialSnapshot.value = formSnapshot()
  dialogVisible.value = true
}

function handleDialogCancel() {
  if (submitLoading.value) return
  if (!isAdminGroup.value && hasUnsavedChanges.value) {
    Modal.confirm({
      title: '放弃未保存的修改？',
      content: '关闭后，本次修改不会保存。',
      okText: '放弃修改',
      okButtonProps: { danger: true },
      onOk: () => {
        dialogVisible.value = false
      },
    })
    return
  }
  dialogVisible.value = false
}

async function submitForm() {
  if (isAdminGroup.value || submitLoading.value) return
  const validation = await formRef.value?.validate().catch(() => false)
  if (!validation) return

  if (selectedHighRisk.value.length) {
    Modal.confirm({
      title: '确认授予高风险权限？',
      content: `当前选择了 ${selectedHighRisk.value.length} 项高风险权限。请确认这符合用户组的职责。`,
      okText: '确认保存',
      okButtonProps: { danger: true },
      onOk: persistForm,
    })
    return
  }
  await persistForm()
}

async function persistForm() {
  submitLoading.value = true
  const payload = {
    name: form.name.trim(),
    description: form.description.trim() || null,
    menu_ids: form.menu_ids,
    permission_keys: form.permission_keys,
  }
  const res =
    dialogMode.value === 'create'
      ? await createGroup(payload)
      : await updateGroup(currentGroup.value!.id, payload)
  submitLoading.value = false

  if (!res.ok) {
    message.error(res.msg || '保存失败')
    return
  }

  message.success('保存成功')
  dialogVisible.value = false
  await fetchGroups()
  await userStore.fetchProfile()
  await userStore.fetchMenus()
  syncDynamicRoutes(userStore.menus)
}

function handleDelete(row: GroupItem) {
  Modal.confirm({
    title: '删除用户组',
    content: `确认删除用户组「${row.name}」？`,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { danger: true },
    async onOk() {
      const res = await deleteGroup(row.id)
      if (!res.ok) {
        message.error(res.msg || '删除失败')
        return Promise.reject()
      }

      message.success('删除成功')
      if (tableData.value.length === 1 && queryForm.pageNum > 1) {
        queryForm.pageNum -= 1
      }
      await fetchGroups()
      return Promise.resolve()
    },
  })
}

onMounted(async () => {
  await fetchMenuTree()
  await fetchOperationPermissions()
  await fetchGroups()
})
</script>

<style lang="scss" scoped>
.group-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  min-height: 0;
}

.dialog-form {
  padding-top: 8px;
  padding-right: 15px;
}

.admin-group-alert {
  margin-bottom: 16px;
}

.menu-tree-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 340px;
  overflow: hidden;
  border: 1px solid var(--ant-color-border);
  border-radius: 6px;

  .menu-tree-box {
    flex: 1;
    height: 0;
    overflow: auto;
  }
}

.menu-tree-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 8px 10px;
  background: var(--ant-color-fill-quaternary);
  border-bottom: 1px solid var(--ant-color-border-secondary);
}

.menu-tree-count,
.permission-count {
  padding: 6px 10px;
  font-size: 12px;
  color: var(--ant-color-text-secondary);
  border-top: 1px solid var(--ant-color-border-secondary);
}

.menu-tree-search {
  flex: 1;
  min-width: 160px;
}

.menu-tree {
  padding: 6px 4px;
  background: var(--ant-color-bg-container);
}

.menu-tree-hit {
  font-weight: 600;
  color: var(--ant-color-primary);
}

.risk-alert {
  margin-bottom: 16px;
}

.permission-area {
  min-width: 0;
  border: 1px solid var(--ant-color-border);
  border-radius: 6px;
}

.permission-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  color: var(--ant-color-text-secondary);
  background: var(--ant-color-fill-quaternary);
  border-bottom: 1px solid var(--ant-color-border-secondary);
}

.permission-hint {
  margin: 8px;
}

@media (width <= 640px) {
  .menu-tree-wrapper {
    height: 300px;
  }
}
</style>
