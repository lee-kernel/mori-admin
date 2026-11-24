<template>
  <PageLayout
    scroll="region"
    description="查看登录、登录失败与退出记录，并按用户、来源和时间筛选。">
    <template #filter>
      <PageFilterBar>
        <template #basic>
          <a-input v-model:value="queryForm.trace_id" placeholder="追踪 ID" allow-clear />
          <a-input v-model:value="queryForm.username" placeholder="用户名" allow-clear />
          <a-input v-model:value="queryForm.ip_address" placeholder="源地址" allow-clear />
          <a-input v-model:value="queryForm.platform" placeholder="平台" allow-clear />
          <a-select v-model:value="queryForm.event_type" placeholder="事件类型" allow-clear>
            <a-select-option :value="1">登录</a-select-option>
            <a-select-option :value="2">退出</a-select-option>
            <a-select-option :value="3">登录失败</a-select-option>
          </a-select>
          <a-range-picker
            v-model:value="dateRange"
            :placeholder="['开始时间', '结束时间']"
            show-time
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            @change="handleDateChange" />
        </template>
        <template #submit>
          <a-button type="primary" @click="handleSearch">
            <template #icon><SearchOutlined /></template>
            查询
          </a-button>
          <a-button @click="handleReset">重置</a-button>
        </template>
      </PageFilterBar>
    </template>
    <div class="login-log-page">
      <a-alert v-if="loadError" type="error" show-icon :message="loadError" class="page-error">
        <template #action><a-button size="small" @click="fetchLoginLogs">重试</a-button></template>
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
            <template v-else-if="column.key === 'username'">
              {{ record.username || '-' }}
            </template>
            <template v-else-if="column.key === 'ip_address'">
              {{ record.ip_address || '-' }}
            </template>
            <template v-else-if="column.key === 'event_type'">
              <a-tag
                v-if="eventTypeMeta(record.event_type)"
                :color="eventTypeMeta(record.event_type)?.color">
                {{ eventTypeMeta(record.event_type)?.label }}
              </a-tag>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'platform'">
              {{ record.platform || '-' }}
            </template>
            <template v-else-if="column.key === 'browser'">
              {{ record.browser || '-' }}
            </template>
            <template v-else-if="column.key === 'login_at'">
              {{ formatTimestamp(record.login_at) }}
            </template>
          </template>
        </a-table>

        <template #footer>
          <a-pagination
            v-model:current="queryForm.pageNum"
            v-model:page-size="queryForm.pageSize"
            show-size-changer
            :page-size-options="['10', '20', '50', '100']"
            :total="total"
            :show-total="(totalCount) => `共 ${totalCount} 条`"
            @change="fetchLoginLogs"
            @show-size-change="fetchLoginLogs" />
        </template>
      </TableSection>
    </div>
  </PageLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { TableColumnsType } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import TableSection from '@/components/TableSection/index.vue'
import PageLayout from '@/components/PageLayout/index.vue'
import PageFilterBar from '@/components/PageFilterBar/index.vue'
import { getLoginLogPage, type LoginLogItem } from '@/api/audit'
import { formatTimestamp, localDateTimeToUtcIso } from '@/utils/datetime'

const loading = ref(false)
const loadError = ref('')
const tableData = ref<LoginLogItem[]>([])
const total = ref(0)
const dateRange = ref<[string, string] | null>(null)

const columns: TableColumnsType = [
  { title: '#', key: 'index', width: 64, fixed: 'left' },
  { title: '追踪 ID', dataIndex: 'trace_id', key: 'trace_id', width: 280, ellipsis: true },
  { title: '用户名', dataIndex: 'username', key: 'username', width: 140, ellipsis: true },
  { title: '源地址', dataIndex: 'ip_address', key: 'ip_address', width: 160 },
  { title: '事件类型', dataIndex: 'event_type', key: 'event_type', width: 100 },
  { title: '平台', dataIndex: 'platform', key: 'platform', width: 120 },
  { title: '浏览器', dataIndex: 'browser', key: 'browser', width: 120 },
  { title: '操作时间', dataIndex: 'login_at', key: 'login_at', width: 200 },
]

const queryForm = reactive({
  pageNum: 1,
  pageSize: 10,
  username: '',
  trace_id: '',
  ip_address: '',
  platform: '',
  event_type: undefined as number | undefined,
  start_time: '',
  end_time: '',
})

function eventTypeMeta(eventType: number | null | undefined) {
  if (eventType === 1) return { label: '登录', color: 'green' }
  if (eventType === 2) return { label: '退出', color: 'orange' }
  if (eventType === 3) return { label: '登录失败', color: 'red' }
  return null
}

function handleDateChange(_dates: unknown, dateStrings: [string, string]) {
  queryForm.start_time = dateStrings[0] || ''
  queryForm.end_time = dateStrings[1] || ''
}

async function fetchLoginLogs() {
  loading.value = true
  loadError.value = ''
  const res = await getLoginLogPage({
    pageNum: queryForm.pageNum,
    pageSize: queryForm.pageSize,
    trace_id: queryForm.trace_id.trim() || undefined,
    username: queryForm.username.trim() || undefined,
    ip_address: queryForm.ip_address.trim() || undefined,
    platform: queryForm.platform.trim() || undefined,
    event_type: queryForm.event_type,
    start_time: localDateTimeToUtcIso(queryForm.start_time),
    end_time: localDateTimeToUtcIso(queryForm.end_time),
  })
  loading.value = false

  if (!res.ok || !res.data) {
    loadError.value = res.msg || '获取登录日志失败'
    return
  }

  tableData.value = res.data.list
  total.value = res.data.total
}

function handleSearch() {
  queryForm.pageNum = 1
  fetchLoginLogs()
}

function handleReset() {
  queryForm.username = ''
  queryForm.trace_id = ''
  queryForm.ip_address = ''
  queryForm.platform = ''
  queryForm.event_type = undefined
  queryForm.start_time = ''
  queryForm.end_time = ''
  dateRange.value = null
  queryForm.pageNum = 1
  fetchLoginLogs()
}

onMounted(() => {
  fetchLoginLogs()
})
</script>

<style lang="scss" scoped>
.login-log-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  min-height: 0;
}
</style>
