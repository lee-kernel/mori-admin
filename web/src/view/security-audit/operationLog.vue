<template>
  <PageLayout scroll="region" description="检索操作记录，追踪业务动作和请求结果。">
    <template #filter>
      <PageFilterBar>
        <template #basic>
          <a-input v-model:value="queryForm.trace_id" placeholder="追踪 ID" allow-clear />
          <a-input v-model:value="queryForm.username" placeholder="用户名" allow-clear />
          <a-input v-model:value="queryForm.title" placeholder="业务动作" allow-clear />
          <a-select v-model:value="queryForm.method" placeholder="请求方法" allow-clear>
            <a-select-option value="GET">GET</a-select-option>
            <a-select-option value="POST">POST</a-select-option>
            <a-select-option value="PUT">PUT</a-select-option>
            <a-select-option value="DELETE">DELETE</a-select-option>
            <a-select-option value="PATCH">PATCH</a-select-option>
          </a-select>
          <a-select v-model:value="queryForm.status_code" placeholder="状态" allow-clear>
            <a-select-option :value="200">200</a-select-option>
            <a-select-option :value="400">400</a-select-option>
            <a-select-option :value="401">401</a-select-option>
            <a-select-option :value="403">403</a-select-option>
            <a-select-option :value="404">404</a-select-option>
            <a-select-option :value="500">500</a-select-option>
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
    <div class="operation-log-page">
      <a-alert v-if="loadError" type="error" show-icon :message="loadError" class="page-error">
        <template #action>
          <a-button size="small" @click="fetchOperationLogs">重试</a-button>
        </template>
      </a-alert>
      <TableSection>
        <a-table
          :columns="columns"
          :data-source="tableData"
          :loading="loading"
          :pagination="false"
          :scroll="{ x: 1524, y: '100%' }"
          row-key="id"
          size="middle">
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.key === 'index'">
              {{ (queryForm.pageNum - 1) * queryForm.pageSize + index + 1 }}
            </template>
            <template v-else-if="column.key === 'username'">
              {{ record.username || '-' }}
            </template>
            <template v-else-if="column.key === 'title'">
              <a-tooltip v-if="record.title" :mouse-enter-delay="1" :title="record.title">
                <span class="url-cell" tabindex="0">{{ record.title }}</span>
              </a-tooltip>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'method'">
              <a-tag :color="methodColor(record.method)">
                {{ record.method || '-' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'url'">
              <a-tooltip v-if="record.url" :mouse-enter-delay="1" :title="record.url">
                <span class="url-cell" tabindex="0">{{ record.url }}</span>
              </a-tooltip>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'status_code'">
              <a-tag :color="statusColor(record.status_code)">
                {{ record.status_code }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'duration_ms'">{{ record.duration_ms }}ms</template>
            <template v-else-if="column.key === 'operated_at'">
              {{ formatTimestamp(record.operated_at) }}
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
            @change="fetchOperationLogs"
            @show-size-change="fetchOperationLogs" />
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
import { getOperationLogPage, type OperationLogItem } from '@/api/audit'
import { formatTimestamp, localDateTimeToUtcIso } from '@/utils/datetime'

const loading = ref(false)
const loadError = ref('')
const tableData = ref<OperationLogItem[]>([])
const total = ref(0)
const dateRange = ref<[string, string] | null>(null)

const columns: TableColumnsType = [
  { title: '#', key: 'index', width: 64, fixed: 'left' },
  { title: '追踪 ID', dataIndex: 'trace_id', key: 'trace_id', width: 280, ellipsis: true },
  { title: '用户名', dataIndex: 'username', key: 'username', width: 140, ellipsis: true },
  { title: '业务动作', dataIndex: 'title', key: 'title', width: 240, ellipsis: true },
  { title: '请求方法', dataIndex: 'method', key: 'method', width: 100 },
  {
    title: '请求接口',
    dataIndex: 'url',
    key: 'url',
    width: 300,
    ellipsis: true,
  },
  { title: '状态', dataIndex: 'status_code', key: 'status_code', width: 100 },
  { title: '耗时', dataIndex: 'duration_ms', key: 'duration_ms', width: 100, align: 'right' },
  {
    title: '操作时间',
    dataIndex: 'operated_at',
    key: 'operated_at',
    width: 200,
  },
]

const queryForm = reactive({
  pageNum: 1,
  pageSize: 10,
  username: '',
  trace_id: '',
  method: '',
  status_code: undefined as number | undefined,
  title: '',
  start_time: '',
  end_time: '',
})

function methodColor(method: string): string {
  const colors: Record<string, string> = {
    GET: 'blue',
    POST: 'green',
    PUT: 'orange',
    DELETE: 'red',
    PATCH: 'purple',
  }
  return colors[method] || 'default'
}

function statusColor(code: number): string {
  if (code >= 200 && code < 300) return 'success'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'error'
  return 'default'
}

function handleDateChange(_dates: unknown, dateStrings: [string, string]) {
  queryForm.start_time = dateStrings[0] || ''
  queryForm.end_time = dateStrings[1] || ''
}

async function fetchOperationLogs() {
  loading.value = true
  loadError.value = ''
  const res = await getOperationLogPage({
    pageNum: queryForm.pageNum,
    pageSize: queryForm.pageSize,
    trace_id: queryForm.trace_id.trim() || undefined,
    username: queryForm.username.trim() || undefined,
    method: queryForm.method || undefined,
    status_code: queryForm.status_code,
    title: queryForm.title.trim() || undefined,
    start_time: localDateTimeToUtcIso(queryForm.start_time),
    end_time: localDateTimeToUtcIso(queryForm.end_time),
  })
  loading.value = false

  if (!res.ok || !res.data) {
    loadError.value = res.msg || '获取操作记录失败'
    return
  }

  tableData.value = res.data.list
  total.value = res.data.total
}

function handleSearch() {
  queryForm.pageNum = 1
  fetchOperationLogs()
}

function handleReset() {
  queryForm.username = ''
  queryForm.trace_id = ''
  queryForm.method = ''
  queryForm.status_code = undefined
  queryForm.title = ''
  queryForm.start_time = ''
  queryForm.end_time = ''
  dateRange.value = null
  queryForm.pageNum = 1
  fetchOperationLogs()
}

onMounted(() => {
  fetchOperationLogs()
})
</script>

<style lang="scss" scoped>
.operation-log-page {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  min-height: 0;
}

.url-cell {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
