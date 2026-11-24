<template>
  <div class="permission-matrix-scroll">
    <table class="permission-matrix">
      <thead>
        <tr>
          <th scope="col">模块</th>
          <th v-for="operation in operations" :key="operation.key" scope="col">
            <a-checkbox
              :checked="isChecked(selectableForOperation(operation.key))"
              :indeterminate="isIndeterminate(selectableForOperation(operation.key))"
              :disabled="readonly || !selectableForOperation(operation.key).length"
              @change="toggle(selectableForOperation(operation.key), $event.target.checked)">
              <span :class="{ 'risk-label': operation.highRisk }">{{ operation.label }}</span>
              <a-tooltip v-if="operation.highRisk" title="高风险操作，保存前请核对授权范围">
                <WarningOutlined class="risk-icon" aria-label="高风险" />
              </a-tooltip>
            </a-checkbox>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="group in groups" :key="group.domain">
          <th scope="row">
            <a-checkbox
              :checked="isChecked(selectable(group.items))"
              :indeterminate="isIndeterminate(selectable(group.items))"
              :disabled="readonly || !selectable(group.items).length"
              @change="toggle(selectable(group.items), $event.target.checked)">
              {{ group.label }}
            </a-checkbox>
          </th>
          <td v-for="operation in operations" :key="operation.key">
            <template v-if="findPermission(group.items, operation.key)">
              <a-tooltip
                :title="
                  findPermission(group.items, operation.key)!.assignable === false
                    ? '你无此权限，无法授予'
                    : ''
                ">
                <span class="permission-cell">
                  <a-checkbox
                    :checked="modelValue.includes(findPermission(group.items, operation.key)!.key)"
                    :disabled="
                      readonly || findPermission(group.items, operation.key)!.assignable === false
                    "
                    :class="{
                      'risk-checkbox': findPermission(group.items, operation.key)!.high_risk,
                    }"
                    :aria-label="findPermission(group.items, operation.key)!.label"
                    @change="
                      toggle([findPermission(group.items, operation.key)!], $event.target.checked)
                    " />
                </span>
              </a-tooltip>
            </template>
            <span v-else class="permission-unavailable">—</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarningOutlined } from '@ant-design/icons-vue'

export interface OperationMatrixItem {
  key: string
  label: string
  domain: string
  domain_label: string
  operation: string
  operation_label: string
  high_risk: boolean
  assignable?: boolean
}

const props = withDefaults(
  defineProps<{
    items: OperationMatrixItem[]
    modelValue: string[]
    readonly?: boolean
  }>(),
  { readonly: false }
)
const emit = defineEmits<{ 'update:modelValue': [keys: string[]] }>()

const groups = computed(() => {
  const map = new Map<string, { domain: string; label: string; items: OperationMatrixItem[] }>()
  for (const item of props.items) {
    if (!map.has(item.domain)) {
      map.set(item.domain, { domain: item.domain, label: item.domain_label, items: [] })
    }
    map.get(item.domain)!.items.push(item)
  }
  return [...map.values()]
})
const operations = computed(() => {
  const map = new Map<string, { key: string; label: string; highRisk: boolean }>()
  for (const item of props.items) {
    const existing = map.get(item.operation)
    if (existing) existing.highRisk ||= item.high_risk
    else {
      map.set(item.operation, {
        key: item.operation,
        label: item.operation_label,
        highRisk: item.high_risk,
      })
    }
  }
  return [...map.values()]
})

function findPermission(items: OperationMatrixItem[], operation: string) {
  return items.find((item) => item.operation === operation)
}

function selectable(items: OperationMatrixItem[]) {
  return items.filter((item) => item.assignable !== false)
}

function selectableForOperation(operation: string) {
  return selectable(props.items.filter((item) => item.operation === operation))
}

function isChecked(items: OperationMatrixItem[]) {
  return items.length > 0 && items.every((item) => props.modelValue.includes(item.key))
}

function isIndeterminate(items: OperationMatrixItem[]) {
  return !isChecked(items) && items.some((item) => props.modelValue.includes(item.key))
}

function toggle(items: OperationMatrixItem[], checked: boolean) {
  if (props.readonly) return
  const selected = new Set(props.modelValue)
  for (const item of selectable(items)) {
    if (checked) selected.add(item.key)
    else selected.delete(item.key)
  }
  emit(
    'update:modelValue',
    props.items.filter((item) => selected.has(item.key)).map((item) => item.key)
  )
}
</script>

<style scoped lang="scss">
.permission-matrix-scroll {
  overflow-x: auto;
}

.permission-matrix {
  width: 100%;
  min-width: 620px;
  text-align: center;
  border-spacing: 0;
  border-collapse: separate;

  th,
  td {
    min-width: 72px;
    padding: 8px;
    border-bottom: 1px solid var(--ant-color-border-secondary);
  }

  th:first-child {
    position: sticky;
    left: 0;
    min-width: 136px;
    text-align: left;
    background: var(--ant-color-bg-container);
  }

  thead th {
    font-weight: 600;
    background:
      linear-gradient(var(--ant-color-fill-quaternary), var(--ant-color-fill-quaternary)),
      var(--ant-color-bg-container);
  }

  thead th:first-child {
    z-index: 1;
  }

  tbody td {
    background: var(--ant-color-bg-container);
  }

  tbody tr:last-child th,
  tbody tr:last-child td {
    border-bottom: 0;
  }
}

.permission-cell {
  display: inline-block;
  min-width: 28px;
}

.risk-label,
.risk-icon {
  color: var(--ant-color-warning-text);
}

.risk-icon {
  margin-left: 4px;
}

.risk-checkbox :deep(.ant-checkbox-inner) {
  border-color: var(--ant-color-warning-border);
}

.risk-checkbox :deep(.ant-checkbox-checked .ant-checkbox-inner) {
  background: var(--ant-color-warning);
  border-color: var(--ant-color-warning);
}

.permission-unavailable {
  color: var(--ant-color-text-disabled);
}
</style>
