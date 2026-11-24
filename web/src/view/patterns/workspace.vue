<template>
  <PageLayout
    title="工作台概览"
    description="标准数据概览与工作台范例：使用 PageLayout 页面滚动、指标卡片栅格、快捷入口与最近动态。">
    <template #actions>
      <PageRefreshButton :loading="refreshing" @click="handleRefresh" />
      <a-button type="primary" @click="router.push('/patterns/drawer-form')">
        <template #icon><PlusOutlined /></template>
        新建任务
      </a-button>
    </template>

    <div class="workspace-page">
      <section class="metric-grid" aria-label="关键指标">
        <a-card v-for="item in metrics" :key="item.key" class="metric-card">
          <div class="metric-header">
            <span class="metric-label">{{ item.label }}</span>
            <a-tag :color="item.tagColor">{{ item.trend }}</a-tag>
          </div>
          <div class="metric-value">{{ item.value }}</div>
          <p class="metric-hint">{{ item.hint }}</p>
        </a-card>
      </section>

      <div class="workspace-columns">
        <a-card title="近期动态" class="workspace-main-card">
          <template #extra>
            <a-segmented v-model:value="activityFilter" :options="activityOptions" size="small" />
          </template>
          <a-list :data-source="filteredActivities" item-layout="horizontal">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :description="item.time">
                  <template #title>
                    <a-space :size="8" wrap>
                      <a-badge :status="item.status" />
                      <span>{{ item.title }}</span>
                      <a-tag>{{ item.category }}</a-tag>
                    </a-space>
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <a-button type="link" size="small" @click="router.push('/patterns/detail')">
                    查看详情
                  </a-button>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-card>

        <a-card title="标准页面范例入口" class="workspace-side-card">
          <div class="quick-links">
            <div
              v-for="entry in quickEntries"
              :key="entry.path"
              class="quick-link-item"
              role="button"
              tabindex="0"
              @click="router.push(entry.path)"
              @keydown.enter="router.push(entry.path)">
              <div class="quick-link-title">{{ entry.title }}</div>
              <p class="quick-link-desc">{{ entry.description }}</p>
            </div>
          </div>
        </a-card>
      </div>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import PageLayout from '@/components/PageLayout/index.vue'
import PageRefreshButton from '@/components/PageRefreshButton/index.vue'

interface MetricItem {
  key: string
  label: string
  value: string
  trend: string
  tagColor: string
  hint: string
}

interface ActivityItem {
  id: number
  title: string
  category: '发布' | '巡检' | '审批'
  status: 'success' | 'processing' | 'warning'
  time: string
}

const router = useRouter()
const refreshing = ref(false)
const activityFilter = ref<'全部' | '发布' | '巡检' | '审批'>('全部')
const activityOptions = ['全部', '发布', '巡检', '审批']

const metrics = ref<MetricItem[]>([
  {
    key: 'active-tasks',
    label: '进行中任务',
    value: '24',
    trend: '+12%',
    tagColor: 'default',
    hint: '较上周新增 3 项关键交付',
  },
  {
    key: 'pass-rate',
    label: 'UI 门禁通过率',
    value: '100%',
    trend: '稳定',
    tagColor: 'success',
    hint: '所有业务页均满足主题与布局约束',
  },
  {
    key: 'pending-review',
    label: '待复核条目',
    value: '6',
    trend: '需关注',
    tagColor: 'warning',
    hint: '建议优先处理 2 项高优先级变更',
  },
  {
    key: 'avg-latency',
    label: '平均响应耗时',
    value: '148 ms',
    trend: '-18 ms',
    tagColor: 'default',
    hint: '近 24 小时 P95 保持平稳',
  },
])

const activities = ref<ActivityItem[]>([
  {
    id: 1,
    title: '完成卡片网格范例页的暗色与窄屏验证',
    category: '巡检',
    status: 'success',
    time: '10 分钟前',
  },
  {
    id: 2,
    title: '发布 UI 静态门禁规则 check:ui v1.0',
    category: '发布',
    status: 'processing',
    time: '1 小时前',
  },
  {
    id: 3,
    title: '待确认：新增详情页分区与操作栏规范',
    category: '审批',
    status: 'warning',
    time: '今天 09:30',
  },
  {
    id: 4,
    title: '同步主题 Token 规范至 AGENTS.md',
    category: '发布',
    status: 'success',
    time: '昨天 18:20',
  },
])

const quickEntries = [
  {
    path: '/patterns/card-grid',
    title: '卡片网格列表页',
    description: '演示 PageFilterBar 高级筛选、CardGridSection 区域滚动与分页。',
  },
  {
    path: '/patterns/detail',
    title: '详情与分区展示页',
    description: '演示 max-width 页面滚动、PageToolbarMore、Descriptions 与 Tabs。',
  },
  {
    path: '/patterns/drawer-form',
    title: '弹窗、抽屉与状态反馈',
    description: '演示 Modal 与 Drawer 选用边界、表单校验及 PageState 三态切换。',
  },
]

const filteredActivities = computed(() => {
  if (activityFilter.value === '全部') return activities.value
  return activities.value.filter((item) => item.category === activityFilter.value)
})

function handleRefresh() {
  refreshing.value = true
  window.setTimeout(() => {
    refreshing.value = false
    message.success('工作台数据已刷新')
  }, 350)
}
</script>

<style scoped lang="scss">
.workspace-page {
  display: flex;
  flex-direction: column;
  gap: var(--mori-admin-section-gap);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--mori-admin-section-gap);
}

.metric-header {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
}

.metric-label {
  font-size: 13px;
  color: var(--ant-color-text-secondary);
}

.metric-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1.25;
  color: var(--ant-color-text);
}

.metric-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--ant-color-text-tertiary);
}

.workspace-columns {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(260px, 1fr);
  gap: var(--mori-admin-section-gap);
  align-items: start;
}

.quick-links {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-link-item {
  padding: 12px 14px;
  cursor: pointer;
  background: var(--ant-color-fill-quaternary);
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: var(--mori-admin-radius-card);
  transition:
    border-color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard),
    background-color var(--mori-admin-motion-fast) var(--mori-admin-ease-standard);
}

.quick-link-item:hover,
.quick-link-item:focus-visible {
  outline: none;
  background: var(--ant-color-fill-tertiary);
  border-color: var(--ant-color-primary);
}

.quick-link-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ant-color-text);
}

.quick-link-desc {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--ant-color-text-secondary);
}

@media (max-width: 960px) {
  .workspace-columns {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
