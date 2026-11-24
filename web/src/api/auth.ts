import { digestPassword } from '@/utils/password'
import { http, type HttpResult } from '@/utils/request'

export interface UserProfile {
  id: number
  username: string
  display_name: string
  email?: string | null
  is_active: boolean
  group_id?: number | null
  group_name?: string | null
  is_admin: boolean
  totp_enabled?: boolean
  menu_ids: number[]
  menu_paths: string[]
  operation_permission_keys: string[]
  last_login_at?: string | null
  last_login_ip?: string | null
}

export interface LoginPayload {
  username: string
  password: string
}

export interface LoginTokenResult {
  access_token: string
  token_type: string
  user: UserProfile
}

export interface LoginResult {
  requires_2fa?: boolean
  access_token?: string | null
  token_type?: string
  user?: UserProfile | null
  challenge_token?: string | null
  challenge_expires_in?: number | null
}

export type TwoFactorMethod = 'totp' | 'recovery'

export interface TwoFactorLoginPayload {
  challenge_token: string
  code: string
  method: TwoFactorMethod
}

export interface TwoFactorStatus {
  enabled: boolean
  enabled_at?: string | null
  recovery_codes_remaining: number
}

export interface TwoFactorSetupResult {
  otpauth_uri: string
  manual_key: string
  expires_in: number
}

export interface TwoFactorRecoveryCodesResult {
  recovery_codes: string[]
}

export async function login(data: LoginPayload): Promise<HttpResult<LoginResult>> {
  const formData = new URLSearchParams()
  formData.set('username', data.username)
  formData.set('password', await digestPassword(data.password))

  return http.post<LoginResult>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
}

export function verifyLoginTwoFactor(
  data: TwoFactorLoginPayload
): Promise<HttpResult<LoginTokenResult>> {
  return http.post<LoginTokenResult>('/auth/login/2fa', data)
}

export function getTwoFactorStatus(): Promise<HttpResult<TwoFactorStatus>> {
  return http.get<TwoFactorStatus>('/users/me/2fa')
}

export async function setupTwoFactor(
  currentPassword: string
): Promise<HttpResult<TwoFactorSetupResult>> {
  return http.post<TwoFactorSetupResult>('/users/me/2fa/setup', {
    current_password: await digestPassword(currentPassword),
  })
}

export function enableTwoFactor(code: string): Promise<HttpResult<TwoFactorRecoveryCodesResult>> {
  return http.post<TwoFactorRecoveryCodesResult>('/users/me/2fa/enable', { code })
}

export async function disableTwoFactor(data: {
  current_password: string
  code: string
  method: TwoFactorMethod
}): Promise<HttpResult<void>> {
  return http.post<void>('/users/me/2fa/disable', {
    current_password: await digestPassword(data.current_password),
    code: data.code,
    method: data.method,
  })
}

export async function regenerateTwoFactorRecoveryCodes(data: {
  current_password: string
  code: string
}): Promise<HttpResult<TwoFactorRecoveryCodesResult>> {
  return http.post<TwoFactorRecoveryCodesResult>('/users/me/2fa/recovery-codes/regenerate', {
    current_password: await digestPassword(data.current_password),
    code: data.code,
  })
}

export function getCurrentUser(): Promise<HttpResult<UserProfile>> {
  return http.get<UserProfile>('/users/me')
}

export function updateCurrentUserProfile(data: {
  display_name: string
  email: string | null
}): Promise<HttpResult<UserProfile>> {
  return http.put<UserProfile>('/users/me', data)
}

/** 上传原始图片，后端校验并转换为 Base64 头像。 */
export async function updateCurrentUserPassword(data: {
  current_password: string
  new_password: string
}): Promise<HttpResult<void>> {
  return http.put<void>('/users/me/password', {
    current_password: await digestPassword(data.current_password),
    new_password: await digestPassword(data.new_password),
  })
}

export function logout(): Promise<HttpResult<void>> {
  return http.post<void>('/auth/logout')
}
