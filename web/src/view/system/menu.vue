<template>
  <PageLayout scroll="region" description="维护导航菜单及其页面入口。">
    <template #actions>
      <a-button v-if="canManage('create')" type="primary" @click="openCreateDialog()">
        <template #icon><PlusOutlined /></template>
        新增菜单
      </a-button>
    </template>
    <template #filter>
      <PageFilterBar>
        <template #basic>
          <a-input-search
            v-model:value="searchValue"
            placeholder="搜索菜单名称或路径"
            allow-clear />
        </template>
        <template #extra>
          <a-button @click="expandAll">展开全部</a-button>
          <a-button @click="collapseAll">折叠全部</a-button>
        </template>
      </PageFilterBar>
    </template>
    <div class="menu-page">
      <a-alert v-if="loadError" type="error" show-icon :message="loadError" class="page-error">
        <template #action><a-button size="small" @click="fetchMenus">重试</a-button></template>
      </a-alert>

      <TableSection>
        <a-table
          class="compact-menu-table"
          :columns="columns"
          :data-source="filteredData"
          :loading="loading"
          :pagination="false"
          :expanded-row-keys="expandedKeys"
          :scroll="{ x: 1500, y: '100%' }"
          row-key="id"
          size="middle"
          @expand="handleExpand"
          @expanded-rows-change="handleExpandedRowsChange">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <a-tooltip :title="record.name" placement="topLeft">
                <span class="cell-ellipsis" :class="{ 'cell-hit': isHit(record) }">
                  {{ record.name }}
                </span>
              </a-tooltip>
            </template>
            <template v-else-if="column.key === 'path'">
              <a-tooltip :title="record.path" placement="topLeft">
                <code class="cell-code cell-ellipsis">{{ record.path }}</code>
              </a-tooltip>
            </template>
            <template v-else-if="column.key === 'permission_key'">
              <a-tooltip
                v-if="record.permission_key"
                :title="record.permission_key"
                placement="topLeft">
                <code class="cell-code cell-ellipsis">{{ record.permission_key }}</code>
              </a-tooltip>
              <span v-else class="muted">-</span>
            </template>
            <template v-else-if="column.key === 'component'">
              <a-tooltip v-if="record.component" :title="record.component" placement="topLeft">
                <code class="cell-code cell-ellipsis">{{ record.component }}</code>
              </a-tooltip>
              <span v-else class="muted">-</span>
            </template>
            <template v-else-if="column.key === 'icon'">
              <a-tag v-if="record.icon">{{ record.icon }}</a-tag>
              <span v-else class="muted">-</span>
            </template>
            <template v-else-if="column.key === 'hidden'">
              <a-tag :color="record.hidden ? 'red' : 'green'">
                {{ record.hidden ? '隐藏' : '显示' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'is_system'">
              <a-tag :color="record.is_system ? 'blue' : 'default'">
                {{ record.is_system ? '系统内置' : '自定义' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <div class="app-table-actions">
                <a-button
                  v-if="canManage('create')"
                  type="link"
                  size="small"
                  @click="openCreateDialog(record)">
                  <template #icon><PlusOutlined /></template>
                  添加子菜单
                </a-button>
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
      </TableSection>

      <a-modal
        v-model:open="dialogVisible"
        :title="dialogTitle"
        width="640px"
        :confirm-loading="submitLoading"
        ok-text="保存"
        cancel-text="取消"
        @ok="submitForm">
        <a-form
          ref="formRef"
          :model="form"
          :rules="rules"
          :label-col="{ style: { width: '96px' } }"
          class="dialog-form">
          <a-form-item label="上级菜单" name="parent_id">
            <a-tree-select
              v-model:value="form.parent_id"
              :tree-data="treeData"
              :field-names="{
                children: 'children',
                label: 'name',
                value: 'id',
              }"
              tree-default-expand-all
              allow-clear
              show-search
              tree-node-filter-prop="name"
              placeholder="作为顶级菜单" />
          </a-form-item>
          <a-form-item label="名称" name="name">
            <a-input v-model:value="form.name" placeholder="如：用户管理" />
          </a-form-item>
          <a-form-item label="路由路径" name="path">
            <a-input v-model:value="form.path" placeholder="如：/system/user" />
          </a-form-item>
          <a-form-item
            label="菜单标识"
            name="permission_key"
            extra="仅用于识别菜单；操作权限在用户组中单独设置。">
            <a-input
              v-model:value="form.permission_key"
              :disabled="dialogMode === 'edit' && Boolean(currentMenu?.is_system)"
              placeholder="如：system:user" />
          </a-form-item>
          <a-form-item label="组件" name="component">
            <a-select
              v-model:value="form.component"
              :options="componentOptions"
              placeholder="请选择组件"
              show-search
              allow-clear
              :filter-option="filterComponentOption" />
          </a-form-item>
          <a-form-item label="重定向" name="redirect">
            <a-input v-model:value="form.redirect" placeholder="可选：/dashboard" />
          </a-form-item>
          <a-form-item label="图标" name="icon">
            <a-input v-model:value="form.icon" placeholder="如：HomeOutlined" />
          </a-form-item>
          <a-form-item label="排序" name="sort">
            <a-input-number v-model:value="form.sort" :min="0" :max="9999" />
          </a-form-item>
          <a-form-item label="状态">
            <a-space>
              <a-checkbox v-model:checked="form.hidden">隐藏</a-checkbox>
              <a-checkbox v-model:checked="form.is_external">外链</a-checkbox>
            </a-space>
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
  createMenu,
  deleteMenu,
  getMenuTree,
  updateMenu,
  type MenuNode,
  type MenuPayload,
} from '@/api/menu'
import PageLayout from '@/components/PageLayout/index.vue'
import PageFilterBar from '@/components/PageFilterBar/index.vue'
import TableSection from '@/components/TableSection/index.vue'
import { syncDynamicRoutes } from '@/router'
import { listAvailableComponents } from '@/router/component-map'
import { useUserStore } from '@/stores/user'

const { message, modal: Modal } = App.useApp()

const userStore = useUserStore()

function canManage(operation: 'create' | 'edit' | 'delete') {
  return (
    userStore.profile?.is_admin &&
    userStore.profile.operation_permission_keys?.includes(`menu.${operation}`)
  )
}
const loading = ref(false)
const loadError = ref('')
const submitLoading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentMenu = ref<MenuNode | null>(null)
const treeData = ref<MenuNode[]>([])
const expandedKeys = ref<number[]>([])
const searchValue = ref('')
const formRef = ref<FormInstance>()

const form = reactive<MenuPayload>({
  parent_id: null,
  name: '',
  path: '',
  permission_key: '',
  component: '',
  icon: '',
  redirect: '',
  sort: 0,
  hidden: false,
  is_external: false,
})

const dialogTitle = computed(() => (dialogMode.value === 'create' ? '新增菜单' : '修改菜单'))
const rules: Record<string, Rule[]> = {
  name: [{ required: true, message: '请输入菜单名称', trigger: 'blur' }],
  path: [{ required: true, message: '请输入路由路径', trigger: 'blur' }],
  permission_key: [
    { required: true, message: '请输入菜单标识', trigger: 'blur' },
    { pattern: /^[a-z0-9][a-z0-9:_-]*$/, message: '仅支持小写字母、数字、冒号、下划线和短横线' },
  ],
  component: [{ required: true, message: '请选择组件', trigger: 'change' }],
}

const componentOptions = listAvailableComponents().map((key) => ({
  label: key,
  value: key,
}))

function filterComponentOption(input: string, option: { value: string }) {
  return option.value.toLowerCase().includes(input.toLowerCase())
}

const columns: TableColumnsType = [
  { title: '名称', key: 'name', dataIndex: 'name', width: 260, fixed: 'left', ellipsis: true },
  { title: '路径', key: 'path', dataIndex: 'path', width: 200, ellipsis: true },
  {
    title: '菜单标识',
    key: 'permission_key',
    dataIndex: 'permission_key',
    width: 190,
    ellipsis: true,
  },
  { title: '组件', key: 'component', dataIndex: 'component', width: 220, ellipsis: true },
  { title: '图标', key: 'icon', width: 110, ellipsis: true },
  { title: '排序', key: 'sort', dataIndex: 'sort', width: 80, align: 'center' },
  { title: '状态', key: 'hidden', width: 90, align: 'center' },
  { title: '类型', key: 'is_system', width: 110, align: 'center' },
  { title: '操作', key: 'actions', width: 240, fixed: 'right' },
]

const flatMenus = computed<MenuNode[]>(() => {
  const list: MenuNode[] = []
  const walk = (nodes: MenuNode[]) => {
    nodes.forEach((node) => {
      list.push(node)
      if (node.children?.length) walk(node.children)
    })
  }
  walk(treeData.value)
  return list
})

function matchKeyword(node: MenuNode, keyword: string) {
  const lower = keyword.trim().toLowerCase()
  if (!lower) return false
  return node.name.toLowerCase().includes(lower) || node.path.toLowerCase().includes(lower)
}

function isHit(node: MenuNode) {
  return Boolean(searchValue.value.trim()) && matchKeyword(node, searchValue.value)
}

// 过滤后的数据：保留命中节点 + 其所有祖先链
const filteredData = computed<MenuNode[]>(() => {
  const keyword = searchValue.value.trim()
  if (!keyword) return treeData.value

  const filterNodes = (nodes: MenuNode[]): MenuNode[] => {
    const result: MenuNode[] = []
    for (const node of nodes) {
      const children = node.children ? filterNodes(node.children) : []
      if (matchKeyword(node, keyword) || children.length) {
        result.push({ ...node, children })
      }
    }
    return result
  }
  return filterNodes(treeData.value)
})

watch(searchValue, (keyword) => {
  if (!keyword.trim()) {
    expandedKeys.value = treeData.value.map((m) => m.id)
    return
  }
  // 搜索时自动展开所有还存在的节点
  const collect = (nodes: MenuNode[], acc: number[]) => {
    nodes.forEach((n) => {
      if (n.children?.length) {
        acc.push(n.id)
        collect(n.children, acc)
      }
    })
  }
  const acc: number[] = []
  collect(filteredData.value, acc)
  expandedKeys.value = acc
})

function handleExpand(expanded: boolean, record: MenuNode) {
  if (expanded) {
    if (!expandedKeys.value.includes(record.id)) {
      expandedKeys.value = [...expandedKeys.value, record.id]
    }
  } else {
    expandedKeys.value = expandedKeys.value.filter((k) => k !== record.id)
  }
}

function handleExpandedRowsChange(keys: readonly (string | number)[]) {
  expandedKeys.value = keys.map((k) => Number(k))
}

function expandAll() {
  expandedKeys.value = flatMenus.value.filter((m) => m.children?.length).map((m) => m.id)
}

function collapseAll() {
  expandedKeys.value = []
}

async function fetchMenus() {
  loading.value = true
  loadError.value = ''
  const res = await getMenuTree()
  loading.value = false
  if (!res.ok || !res.data) {
    loadError.value = res.msg || '获取菜单列表失败'
    return
  }
  treeData.value = res.data.list
  // 默认展开顶层节点
  expandedKeys.value = treeData.value.map((m) => m.id)
}

function resetForm() {
  form.parent_id = null
  form.name = ''
  form.path = ''
  form.permission_key = ''
  form.component = ''
  form.icon = ''
  form.redirect = ''
  form.sort = 0
  form.hidden = false
  form.is_external = false
  formRef.value?.clearValidate()
}

function openCreateDialog(parent?: MenuNode) {
  dialogMode.value = 'create'
  currentMenu.value = null
  resetForm()
  if (parent) {
    form.parent_id = parent.id
  }
  dialogVisible.value = true
}

function openEditDialog(row: MenuNode) {
  dialogMode.value = 'edit'
  currentMenu.value = row
  form.parent_id = row.parent_id ?? null
  form.name = row.name
  form.path = row.path
  form.permission_key = row.permission_key
  form.component = row.component || ''
  form.icon = row.icon || ''
  form.redirect = row.redirect || ''
  form.sort = row.sort
  form.hidden = row.hidden
  form.is_external = row.is_external
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

async function submitForm() {
  const validation = await formRef.value?.validate().catch(() => false)
  if (!validation) return

  submitLoading.value = true
  const payload: MenuPayload = {
    parent_id: form.parent_id,
    name: form.name.trim(),
    path: form.path.trim(),
    permission_key: form.permission_key.trim(),
    component: form.component?.trim() || null,
    icon: form.icon?.trim() || null,
    redirect: form.redirect?.trim() || null,
    sort: form.sort,
    hidden: form.hidden,
    is_external: form.is_external,
  }
  const res =
    dialogMode.value === 'create'
      ? await createMenu(payload)
      : await updateMenu(currentMenu.value!.id, payload)
  submitLoading.value = false

  if (!res.ok) {
    message.error(res.msg || '保存失败')
    return
  }

  message.success('保存成功')
  dialogVisible.value = false
  await fetchMenus()
  await userStore.fetchMenus()
  syncDynamicRoutes(userStore.menus)
}

function handleDelete(row: MenuNode) {
  Modal.confirm({
    title: '删除菜单',
    content: `确认删除菜单「${row.name}」？`,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { danger: true },
    async onOk() {
      const res = await deleteMenu(row.id)
      if (!res.ok) {
        message.error(res.msg || '删除失败')
        return Promise.reject()
      }
      message.success('删除成功')
      await fetchMenus()
      await userStore.fetchMenus()
      return Promise.resolve()
    },
  })
}

onMounted(fetchMenus)
</script>

<style lang="scss" scoped>
.menu-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  min-height: 0;
}

.cell-code {
  display: block;
  max-width: 100%;
  padding: 2px 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12.5px;
  color: var(--ant-color-text);
  background: var(--ant-color-fill-quaternary);
  border-radius: 4px;
}

.cell-ellipsis {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-hit {
  font-weight: 600;
  color: var(--ant-color-primary);
}

.muted {
  color: var(--ant-color-text-tertiary);
}

:deep(.compact-menu-table .ant-table-thead > tr > th),
:deep(.compact-menu-table .ant-table-tbody > tr > td) {
  padding: 9px 12px;
  vertical-align: middle;
}

:deep(.compact-menu-table .ant-tag) {
  margin-inline-end: 0;
  white-space: nowrap;
}

.app-table-actions {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  white-space: nowrap;
}

.dialog-form {
  padding-top: 12px;
}
</style>
