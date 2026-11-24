import { http, type HttpResult } from '@/utils/request'

export interface Branding {
  logo: string | null
}

export function getBranding(): Promise<HttpResult<Branding>> {
  return http.get<Branding>('/system/branding')
}

export function updateLogo(file: File): Promise<HttpResult<Branding>> {
  return http.put<Branding>('/system/branding/logo', file, {
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
  })
}

export function resetLogo(): Promise<HttpResult<Branding>> {
  return http.delete<Branding>('/system/branding/logo')
}
