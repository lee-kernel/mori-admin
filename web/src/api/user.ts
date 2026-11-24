import { digestPassword } from '@/utils/password'
import { http, type HttpResult, type PageResult } from '@/utils/request'

export interface UserItem {
  id: number
  username: string
  display_name: string
  email?: string | null
  is_active: boolean
  group_id?: number | null
  group_name?: string | null
  is_admin: boolean
  totp_enabled?: boolean
  menu_ids?: number[]
}

export interface UserPageParams {
  pageNum: number
  pageSize: number
  keyword?: string
}

export interface CreateUserPayload {
  username: string
  display_name: string
  email?: string | null
  password: string
  is_active: boolean
  group_id?: number | null
}

export interface UpdateUserPayload {
  display_name: string
  email?: string | null
  is_active: boolean
  group_id?: number | null
}

export interface UpdatePasswordPayload {
  password: string
}

export function getUserPage(params: UserPageParams): Promise<HttpResult<PageResult<UserItem>>> {
  return http.get<PageResult<UserItem>>('/users/page', params)
}

export async function createUser(data: CreateUserPayload): Promise<HttpResult<UserItem>> {
  return http.post<UserItem>('/users', {
    ...data,
    password: await digestPassword(data.password),
  })
}

export function updateUser(id: number, data: UpdateUserPayload): Promise<HttpResult<UserItem>> {
  return http.put<UserItem>(`/users/${id}`, data)
}

export async function updateUserPassword(
  id: number,
  data: UpdatePasswordPayload
): Promise<HttpResult<void>> {
  return http.put<void>(`/users/${id}/password`, {
    password: await digestPassword(data.password),
  })
}

export function resetUserTwoFactor(id: number): Promise<HttpResult<void>> {
  return http.delete<void>(`/users/${id}/2fa`)
}

export function deleteUser(id: number): Promise<HttpResult<void>> {
  return http.delete<void>(`/users/${id}`)
}
