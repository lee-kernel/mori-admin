import { http, type HttpResult } from '@/utils/request'

export interface MenuNode {
  id: number
  parent_id?: number | null
  name: string
  path: string
  permission_key: string
  component?: string | null
  icon?: string | null
  redirect?: string | null
  sort: number
  hidden: boolean
  is_external: boolean
  is_system: boolean
  children?: MenuNode[]
}

export type MenuItem = Omit<MenuNode, 'children'>

export interface MenuTreeResult {
  list: MenuNode[]
}

export interface MenuListResult {
  list: MenuItem[]
}

export interface MenuPayload {
  parent_id: number | null
  name: string
  path: string
  permission_key: string
  component?: string | null
  icon?: string | null
  redirect?: string | null
  sort: number
  hidden: boolean
  is_external: boolean
}

export function getMyMenus(): Promise<HttpResult<MenuTreeResult>> {
  return http.get<MenuTreeResult>('/menus/mine')
}

export function getMenuTree(): Promise<HttpResult<MenuTreeResult>> {
  return http.get<MenuTreeResult>('/menus/tree')
}

export function getMenuList(): Promise<HttpResult<MenuListResult>> {
  return http.get<MenuListResult>('/menus/all')
}

export function createMenu(data: MenuPayload): Promise<HttpResult<MenuItem>> {
  return http.post<MenuItem>('/menus', data)
}

export function updateMenu(id: number, data: MenuPayload): Promise<HttpResult<MenuItem>> {
  return http.put<MenuItem>(`/menus/${id}`, data)
}

export function deleteMenu(id: number): Promise<HttpResult<void>> {
  return http.delete<void>(`/menus/${id}`)
}
