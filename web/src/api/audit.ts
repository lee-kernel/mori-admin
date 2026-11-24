import { http, type HttpResult, type PageResult } from '@/utils/request'

export interface LoginLogItem {
  id: number
  trace_id?: string | null
  user_id?: number | null
  username?: string | null
  ip_address?: string | null
  platform?: string | null
  browser?: string | null
  event_type: number // 1: login, 2: logout
  login_at?: string | null
}

export interface LoginLogPageParams {
  pageNum: number
  pageSize: number
  trace_id?: string
  username?: string
  ip_address?: string
  platform?: string
  event_type?: number
  start_time?: string
  end_time?: string
}

export interface OperationLogItem {
  id: number
  trace_id?: string | null
  user_id?: number | null
  username?: string | null
  method?: string | null
  url?: string | null
  title?: string | null
  status_code: number
  duration_ms: number
  operated_at?: string | null
}

export interface OperationLogPageParams {
  pageNum: number
  pageSize: number
  trace_id?: string
  username?: string
  method?: string
  status_code?: number
  title?: string
  start_time?: string
  end_time?: string
}

export function getLoginLogPage(
  params: LoginLogPageParams
): Promise<HttpResult<PageResult<LoginLogItem>>> {
  return http.get<PageResult<LoginLogItem>>('/audit/login-log/page', params)
}

export function getOperationLogPage(
  params: OperationLogPageParams
): Promise<HttpResult<PageResult<OperationLogItem>>> {
  return http.get<PageResult<OperationLogItem>>('/audit/operation-log/page', params)
}
