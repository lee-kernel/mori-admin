import { http, type HttpResult, type PageResult } from '@/utils/request'

export interface GroupItem {
  id: number
  name: string
  description?: string | null
  menu_ids: number[]
  permission_keys: string[]
  is_system: boolean
  is_admin: boolean
}

export interface GroupPageParams {
  pageNum: number
  pageSize: number
  keyword?: string
}

export interface GroupPayload {
  name: string
  description?: string | null
  menu_ids: number[]
  permission_keys: string[]
}

export interface OperationPermission {
  key: string
  label: string
  domain: string
  domain_label: string
  operation: 'read' | 'create' | 'edit' | 'delete' | 'run' | 'manage'
  operation_label: string
  high_risk: boolean
}

export function getOperationPermissions(): Promise<HttpResult<OperationPermission[]>> {
  return http.get<OperationPermission[]>('/groups/permissions')
}

export interface GroupOptions {
  groups: GroupItem[]
}

export function getGroupPage(params: GroupPageParams): Promise<HttpResult<PageResult<GroupItem>>> {
  return http.get<PageResult<GroupItem>>('/groups/page', params)
}

export function getGroupOptions(): Promise<HttpResult<GroupOptions>> {
  return http.get<GroupOptions>('/groups/options')
}

export function createGroup(data: GroupPayload): Promise<HttpResult<GroupItem>> {
  return http.post<GroupItem>('/groups', data)
}

export function updateGroup(id: number, data: GroupPayload): Promise<HttpResult<GroupItem>> {
  return http.put<GroupItem>(`/groups/${id}`, data)
}

export function deleteGroup(id: number): Promise<HttpResult<void>> {
  return http.delete<void>(`/groups/${id}`)
}
