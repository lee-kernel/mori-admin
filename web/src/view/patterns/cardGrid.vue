<template>
  <PageLayout
    title="卡片网格列表"
    description="标准卡片列表范例：复用 PageLayout scroll='region'、PageFilterBar 高级筛选、CardGridSection 与 PageState。"
    scroll="region">
    <template #actions>
      <a-segmented v-model:value="demoState" :options="stateOptions" />
      <PageRefreshButton :loading="demoState === 'loading'" @click="handleReset" />
    </template>

    <template #filter>
      <PageFilterBar v-model:expanded="advancedExpanded" advanced>
        <template #basic>
          <a-input
            v-model:value="query.keyword"
            class="page-filter-search"
            placeholder="搜索模板名称或描述"
            allow-clear
            @press-enter="handleSearch" />
          <a-select v-model:value="query.category" placeholder="全部分类" allow-clear>
            <a-select-option value="布局">布局</a-select-option>
            <a-select-option value="表单">表单</a-select-option>
            <a-select-option value="数据">数据</a-select-option>
          </a-select>
        </template>
        <template #submit>
          <a-button type="primary" @click="handleSearch">
            <template #icon><SearchOutlined /></template>
            查询
          </a-button>
          <a-button @click="handleReset">重置</a-button>
        </template>
        <template #advanced>
          <a-select v-model:value="query.status" placeholder="状态" allow-clear>
            <a-select-option value="ready">可用</a-select-option>
            <a-select-option value="beta">试点</a-select-option>
          </a-select>
        </template>
      </PageFilterBar>
    </template>

    <div class="card-grid-page">
      <PageState v-if="demoState === 'loading'" kind="loading" description="正在加载卡片列表…" />
      <PageState
        v-else-if="demoState === 'error'"
        kind="error"
        title="加载失败"
        description="模拟网络异常场景，点击下方按钮可恢复正常视图。">
        <template #actions>
          <a-button type="primary" @click="demoState = 'normal'">重试</a-button>
        </template>
      </PageState>
      <PageState
        v-else-if="pagedItems.length === 0"
        kind="empty"
        title="未找到匹配的卡片"
        description="尝试调整筛选条件，或重置筛选查看全部条目。">
        <template #actions>
          <a-button type="primary" @click="handleReset">重置筛选</a-button>
        </template>
      </PageState>

      <CardGridSection v-else ref="gridRef">
        <div class="pattern-card-grid">
          <a-card v-for="item in pagedItems" :key="item.id" hoverable class="pattern-card">
            <template #title>
              <span class="pattern-card-title">{{ item.title }}</span>
            </template>
            <template #extra>
              <a-tag :color="item.status === 'ready' ? 'green' : 'blue'">
                {{ item.status === 'ready' ? '可用' : '试点' }}
              </a-tag>
            </template>
            <p class="pattern-card-desc">{{ item.description }}</p>
            <div class="pattern-card-meta">
              <a-tag>{{ item.category }}</a-tag>
              <span class="pattern-card-owner">{{ item.owner }}</span>
            </div>
            <template #actions>
              <a-button type="link" size="small" @click="router.push('/patterns/detail')">
                查看详情
              </a-button>
              <a-button type="link" size="small" @click="handleInspect(item)">预览提示</a-button>
            </template>
          </a-card>
        </div>

        <template #footer>
          <a-pagination
            v-model:current="query.pageNum"
            v-model:page-size="query.pageSize"
            show-size-changer
            :page-size-options="['6', '12', '24']"
            :total="filteredItems.length"
            :show-total="(count) => `共 ${count} 条`"
            @change="handlePageChange" />
        </template>
      </CardGridSection>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import PageLayout from '@/components/PageLayout/index.vue'
import PageFilterBar from '@/components/PageFilterBar/index.vue'
import CardGridSection from '@/components/CardGridSection/index.vue'
import PageState from '@/components/PageState/index.vue'
import PageRefreshButton from '@/components/PageRefreshButton/index.vue'

interface PatternCardItem {
  id: number
  title: string
  category: '布局' | '表单' | '数据'
  status: 'ready' | 'beta'
  owner: string
  description: string
}

const router = useRouter()
const gridRef = ref<InstanceType<typeof CardGridSection> | null>(null)
const advancedExpanded = ref(false)
const demoState = ref<'normal' | 'loading' | 'error'>('normal')

const stateOptions = [
  { label: '正常', value: 'normal' },
  { label: '加载态', value: 'loading' },
  { label: '错误态', value: 'error' },
]

const query = reactive({
  keyword: '',
  category: undefined as string | undefined,
  status: undefined as string | undefined,
  pageNum: 1,
  pageSize: 6,
})

const allItems: PatternCardItem[] = [
  {
    id: 1,
    title: '标准表格列表页',
    category: '数据',
    status: 'ready',
    owner: '核心规范',
    description: '适用于查询筛选、表体区域滚动与底部分页的标准数据列表。',
  },
  {
    id: 2,
    title: '卡片网格列表页',
    category: '布局',
    status: 'ready',
    owner: '核心规范',
    description: '适用于视觉卡片、模板市场、资源库等网格浏览场景，自带滚动与固定分页。',
  },
  {
    id: 3,
    title: '详情与分区展示页',
    category: '布局',
    status: 'ready',
    owner: '核心规范',
    description: '适用于对象详情查看，结合 Descriptions、Tabs 与工具栏操作区。',
  },
  {
    id: 4,
    title: '抽屉编辑表单',
    category: '表单',
    status: 'ready',
    owner: '交互规范',
    description: '字段超过 6 项或需要分组填写时优先使用 Drawer，保持上下文可见。',
  },
  {
    id: 5,
    title: '轻量确认弹窗',
    category: '表单',
    status: 'ready',
    owner: '交互规范',
    description: '3~5 个字段的快速新建或状态变更使用 Modal，避免过度打断。',
  },
  {
    id: 6,
    title: '页面级三态反馈',
    category: '布局',
    status: 'ready',
    owner: '交互规范',
    description: '统一加载中、空数据与错误重试的反馈结构，避免页面空白。',
  },
  {
    id: 7,
    title: '工作台概览页',
    category: '数据',
    status: 'beta',
    owner: '视觉规范',
    description: '使用指标卡片与双栏布局组织首页关键信息与快捷任务入口。',
  },
  {
    id: 8,
    title: '设置与资料表单页',
    category: '表单',
    status: 'ready',
    owner: '交互规范',
    description: '单列定宽卡片承载配置表单，字段错误即时提示并保留可重试输入。',
  },
]

const filteredItems = computed(() => {
  const kw = query.keyword.trim().toLowerCase()
  return allItems.filter((item) => {
    if (query.category && item.category !== query.category) return false
    if (query.status && item.status !== query.status) return false
    if (
      kw &&
      !item.title.toLowerCase().includes(kw) &&
      !item.description.toLowerCase().includes(kw)
    )
      return false
    return true
  })
})

const pagedItems = computed(() => {
  const start = (query.pageNum - 1) * query.pageSize
  return filteredItems.value.slice(start, start + query.pageSize)
})

function handleSearch() {
  query.pageNum = 1
  demoState.value = 'normal'
  gridRef.value?.scrollToTop()
}

function handleReset() {
  query.keyword = ''
  query.category = undefined
  query.status = undefined
  query.pageNum = 1
  demoState.value = 'normal'
  gridRef.value?.scrollToTop()
}

function handlePageChange() {
  gridRef.value?.scrollToTop()
}

function handleInspect(item: PatternCardItem) {
  message.info(`已选中范例：${item.title}`)
}
</script>

<style scoped lang="scss">
.card-grid-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  min-height: 0;
}

.pattern-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--mori-admin-section-gap);
}

.pattern-card {
  display: flex;
  flex-direction: column;
}

.pattern-card-title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.pattern-card-desc {
  min-height: 44px;
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--ant-color-text-secondary);
}

.pattern-card-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
}

.pattern-card-owner {
  font-size: 12px;
  color: var(--ant-color-text-tertiary);
}
</style>
