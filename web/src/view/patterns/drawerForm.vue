<template>
  <PageLayout
    title="弹窗、抽屉与状态反馈"
    description="演示 Modal 与 Drawer 的选用边界、表单防重复提交、危险确认与 PageState 三态用法。"
    max-width="1120px">
    <template #actions>
      <a-button @click="modalOpen = true">打开轻量弹窗（Modal）</a-button>
      <a-button type="primary" @click="drawerOpen = true">打开多字段抽屉（Drawer）</a-button>
    </template>

    <div class="drawer-form-page">
      <a-card title="交互容器选用边界">
        <div class="boundary-grid">
          <div class="boundary-item">
            <h3>何时用 Modal（弹窗）</h3>
            <p>字段 ≤ 5 项、单步完成、聚焦决策的轻量操作（例如重命名、快速新建、状态切换）。</p>
            <a-space wrap>
              <a-button @click="modalOpen = true">体验轻量弹窗</a-button>
              <a-popconfirm
                title="确认执行此危险操作吗？"
                ok-text="确认删除"
                cancel-text="取消"
                ok-type="danger"
                @confirm="handleDangerousConfirm">
                <a-button danger>危险操作确认（Popconfirm）</a-button>
              </a-popconfirm>
            </a-space>
          </div>

          <div class="boundary-item">
            <h3>何时用 Drawer（抽屉）</h3>
            <p>字段较多、需要分节说明或边看列表边编辑时使用，避免弹窗高度溢出。</p>
            <a-button @click="drawerOpen = true">体验多字段抽屉</a-button>
          </div>
        </div>
      </a-card>

      <a-card title="PageState 页面级状态反馈示范">
        <template #extra>
          <a-segmented v-model:value="previewState" :options="stateOptions" size="small" />
        </template>
        <PageState
          v-if="previewState === 'loading'"
          kind="loading"
          description="正在同步配置数据…" />
        <PageState
          v-else-if="previewState === 'empty'"
          kind="empty"
          title="暂无记录"
          description="点击右上角按钮创建第一条配置。">
          <template #actions>
            <a-button type="primary" @click="modalOpen = true">立即创建</a-button>
          </template>
        </PageState>
        <PageState
          v-else
          kind="error"
          title="服务暂时不可用"
          description="请检查网络连接或稍后重试。">
          <template #actions>
            <a-button type="primary" @click="previewState = 'loading'">重新加载</a-button>
          </template>
        </PageState>
      </a-card>

      <a-modal
        v-model:open="modalOpen"
        title="快速新建条目"
        :confirm-loading="modalSubmitting"
        destroy-on-close
        @ok="submitModal">
        <a-form ref="modalFormRef" :model="modalForm" layout="vertical">
          <a-form-item
            label="名称"
            name="name"
            :rules="[{ required: true, message: '请输入条目名称' }]">
            <a-input v-model:value="modalForm.name" placeholder="例如：公告列表页" />
          </a-form-item>
          <a-form-item label="页面类型" name="layoutType">
            <a-radio-group v-model:value="modalForm.layoutType">
              <a-radio value="table">表格列表</a-radio>
              <a-radio value="card">卡片网格</a-radio>
              <a-radio value="form">设置表单</a-radio>
            </a-radio-group>
          </a-form-item>
        </a-form>
      </a-modal>

      <a-drawer
        v-model:open="drawerOpen"
        title="编辑完整配置"
        :width="drawerWidth"
        destroy-on-close>
        <a-form ref="drawerFormRef" :model="drawerForm" layout="vertical" @finish="submitDrawer">
          <a-form-item
            label="模块名称"
            name="title"
            :rules="[{ required: true, message: '请输入模块名称' }]">
            <a-input v-model:value="drawerForm.title" placeholder="请输入模块名称" />
          </a-form-item>
          <a-form-item
            label="路由路径"
            name="routePath"
            :rules="[{ required: true, message: '请输入路由路径' }]">
            <a-input v-model:value="drawerForm.routePath" placeholder="/orders/list" />
          </a-form-item>
          <a-form-item label="滚动策略" name="scrollMode">
            <a-select v-model:value="drawerForm.scrollMode">
              <a-select-option value="page">页面滚动（详情/表单）</a-select-option>
              <a-select-option value="region">区域滚动（表格/卡片列表）</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="启用暗色模式验收" name="verifyDark">
            <a-switch v-model:checked="drawerForm.verifyDark" />
          </a-form-item>
          <a-form-item label="补充说明" name="remark">
            <a-textarea
              v-model:value="drawerForm.remark"
              :rows="3"
              placeholder="记录页面交互要求或待确认项" />
          </a-form-item>
        </a-form>

        <template #footer>
          <div class="drawer-footer">
            <a-button @click="drawerOpen = false">取消</a-button>
            <a-button type="primary" :loading="drawerSubmitting" @click="triggerDrawerSubmit">
              保存配置
            </a-button>
          </div>
        </template>
      </a-drawer>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { message, type FormInstance } from 'ant-design-vue'
import PageLayout from '@/components/PageLayout/index.vue'
import PageState from '@/components/PageState/index.vue'

const previewState = ref<'empty' | 'loading' | 'error'>('empty')
const stateOptions = [
  { label: '空状态', value: 'empty' },
  { label: '加载中', value: 'loading' },
  { label: '错误态', value: 'error' },
]

const modalOpen = ref(false)
const modalSubmitting = ref(false)
const modalFormRef = ref<FormInstance>()
const modalForm = reactive({
  name: '',
  layoutType: 'table',
})

const drawerOpen = ref(false)
const drawerSubmitting = ref(false)
const drawerFormRef = ref<FormInstance>()
const drawerForm = reactive({
  title: '公告管理',
  routePath: '/content/notices',
  scrollMode: 'region',
  verifyDark: true,
  remark: '',
})

const drawerWidth = computed(() => 'min(520px, 100vw)')

async function submitModal() {
  if (!modalFormRef.value) return
  try {
    await modalFormRef.value.validate()
  } catch {
    return
  }
  modalSubmitting.value = true
  window.setTimeout(() => {
    modalSubmitting.value = false
    modalOpen.value = false
    message.success(`已创建：${modalForm.name}`)
    modalForm.name = ''
  }, 300)
}

async function triggerDrawerSubmit() {
  if (!drawerFormRef.value) return
  try {
    await drawerFormRef.value.validate()
  } catch {
    return
  }
  submitDrawer()
}

function submitDrawer() {
  drawerSubmitting.value = true
  window.setTimeout(() => {
    drawerSubmitting.value = false
    drawerOpen.value = false
    message.success(`已保存配置：${drawerForm.title}`)
  }, 300)
}

function handleDangerousConfirm() {
  message.warning('已演示危险操作确认回调')
}
</script>

<style scoped lang="scss">
.drawer-form-page {
  display: flex;
  flex-direction: column;
  gap: var(--mori-admin-section-gap);
}

.boundary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--mori-admin-section-gap);
}

.boundary-item {
  padding: 16px;
  background: var(--ant-color-fill-quaternary);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: var(--mori-admin-radius-card);
}

.boundary-item h3 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--ant-color-text);
}

.boundary-item p {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--ant-color-text-secondary);
}

.drawer-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
