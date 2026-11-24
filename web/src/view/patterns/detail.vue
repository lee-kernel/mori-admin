<template>
  <PageLayout
    title="详情与分区页"
    description="标准详情页范例：PageLayout 页面滚动配合 max-width，使用 Descriptions、Tabs 与工具栏操作区。"
    max-width="1120px">
    <template #actions>
      <a-button @click="router.push('/patterns/card-grid')">返回列表</a-button>
      <PageToolbarMore :items="moreItems" @select="handleMoreAction" />
      <a-button type="primary" @click="router.push('/patterns/drawer-form')">编辑配置</a-button>
    </template>

    <div class="detail-page">
      <a-card title="基础信息">
        <template #extra>
          <a-badge status="success" text="已启用" />
        </template>
        <a-descriptions :column="{ xs: 1, sm: 2, md: 3 }" bordered size="small">
          <a-descriptions-item label="项目标识">mori-ui-framework</a-descriptions-item>
          <a-descriptions-item label="技术栈">Vue 3 + Ant Design Vue</a-descriptions-item>
          <a-descriptions-item label="主题机制">浅色 / 深色 / 跟随系统</a-descriptions-item>
          <a-descriptions-item label="布局原语">PageLayout / PageFilterBar</a-descriptions-item>
          <a-descriptions-item label="静态门禁">npm run check:ui</a-descriptions-item>
          <a-descriptions-item label="视觉自检">npm run verify:ui</a-descriptions-item>
        </a-descriptions>
        <p class="detail-note">
          约束原则：Agent 不引入额外 UI 框架，所有页面统一基于项目既有的 Ant Design Vue
          组件、公共布局组件与主题 Token 实现。
        </p>
      </a-card>

      <a-card>
        <a-tabs v-model:active-key="activeTab">
          <a-tab-pane key="rules" tab="生效规则">
            <a-list :data-source="guardrailRules" item-layout="horizontal">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta :title="item.name" :description="item.detail" />
                  <template #actions>
                    <a-tag color="green">已启用</a-tag>
                  </template>
                </a-list-item>
              </template>
            </a-list>
          </a-tab-pane>

          <a-tab-pane key="changelog" tab="变更记录">
            <a-list :data-source="changeRecords" item-layout="horizontal">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta :title="item.summary" :description="item.time" />
                  <template #actions>
                    <a-tag>{{ item.actor }}</a-tag>
                  </template>
                </a-list-item>
              </template>
            </a-list>
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import PageLayout from '@/components/PageLayout/index.vue'
import PageToolbarMore from '@/components/PageToolbarMore/index.vue'

const router = useRouter()
const activeTab = ref('rules')

const moreItems = [
  { key: 'copy', label: '复制标识' },
  { key: 'export', label: '导出配置说明' },
]

const guardrailRules = [
  {
    name: 'no-extra-ui-framework',
    detail: '禁止引入 Tailwind、Element Plus、Naive UI 等额外 UI 或 CSS 框架。',
  },
  {
    name: 'registered-antd-component',
    detail: '模板中所有 <a-*> 标签必须已在 src/main.ts 注册，避免运行时静默失效。',
  },
  {
    name: 'require-page-layout',
    detail: '所有登录后的业务页面根节点必须使用 PageLayout。',
  },
  {
    name: 'no-hardcoded-color',
    detail: '禁止硬编码颜色值，统一通过 --ant-* 与 --mori-admin-* Token 适配深浅色。',
  },
]

const changeRecords = [
  { summary: '补齐纯前端 UI 范例集与无后端预览模式', time: '今天 20:00', actor: 'Agent' },
  { summary: '新增静态门禁脚本 check:ui 与视觉自检 verify:ui', time: '今天 19:55', actor: 'Agent' },
]

function handleMoreAction(key: string) {
  if (key === 'copy') {
    message.success('已复制项目标识：mori-ui-framework')
    return
  }
  message.info('已触发导出配置说明')
}
</script>

<style scoped lang="scss">
.detail-page {
  display: flex;
  flex-direction: column;
  gap: var(--mori-admin-section-gap);
}

.detail-note {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--ant-color-text-secondary);
}
</style>
