import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type Method,
} from 'axios'
import { useUserStore } from '@/stores/user'

const TOKEN_KEY = 'mori_admin_access_token'

export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message?: string
}

export interface HttpResult<T = unknown> {
  ok: boolean
  data: T | null
  msg: string
  code?: number
  traceId?: string
}

export interface PageResult<T> {
  list: T[]
  total: number
}

const SUCCESS_CODE = 200
const UNAUTHORIZED_CODE = 401
const LOGIN_HASH = '#/login'
const DEFAULT_ERROR_MESSAGE = '请求失败'

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
})

service.interceptors.request.use(
  (config) => {
    config.headers = config.headers || {}
    config.headers.Accept = 'application/json'

    if (!config.headers['Content-Type'] && config.method !== 'get') {
      config.headers['Content-Type'] = 'application/json;charset=UTF-8'
    }

    const token = localStorage.getItem(TOKEN_KEY)
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.code === 'ECONNABORTED') {
      error.message = '请求超时，请稍后重试'
    } else if (!error.response) {
      error.message = '网络异常，请检查连接后重试'
    }
    return Promise.reject(error)
  }
)

function buildResult<T>(
  ok: boolean,
  data: T | null,
  msg: string,
  code?: number,
  traceId?: string
): HttpResult<T> {
  return {
    ok,
    data,
    msg: !ok && traceId ? `${msg}（追踪 ID：${traceId}）` : msg,
    code,
    traceId,
  }
}

function isJsonBlob(blob: Blob): boolean {
  return blob.type.includes('application/json') || blob.type.includes('text/json')
}

async function parseBlobResponse<T>(blob: Blob, traceId?: string): Promise<HttpResult<T>> {
  if (isJsonBlob(blob)) {
    const text = await blob.text()

    try {
      const parsed = JSON.parse(text) as ApiResponse<unknown>
      return buildResult<T>(false, null, parsed.message || '文件下载失败', parsed.code, traceId)
    } catch {
      return buildResult<T>(false, null, text || '文件下载失败', undefined, traceId)
    }
  }

  return buildResult<T>(true, blob as unknown as T, '文件下载成功', SUCCESS_CODE)
}

function redirectToLogin() {
  useUserStore().clearSession()
  if (window.location.hash !== LOGIN_HASH) {
    window.location.hash = LOGIN_HASH
  }
}

function parseApiResponse<T>(payload: ApiResponse<T>, traceId?: string): HttpResult<T> {
  const ok = payload.code === SUCCESS_CODE
  return buildResult(
    ok,
    ok ? payload.data : null,
    payload.message || (ok ? '请求成功' : DEFAULT_ERROR_MESSAGE),
    payload.code,
    traceId
  )
}

function parseError<T>(error: unknown): HttpResult<T> {
  const axiosError = error as AxiosError<ApiResponse<unknown>>
  const code = axiosError.response?.data?.code ?? axiosError.response?.status
  if (code === UNAUTHORIZED_CODE) {
    redirectToLogin()
  }
  return buildResult<T>(
    false,
    null,
    axiosError.response?.data?.message || axiosError?.message || DEFAULT_ERROR_MESSAGE,
    code,
    axiosError.response?.headers?.['x-trace-id']
  )
}

async function request<T = unknown>(config: AxiosRequestConfig): Promise<HttpResult<T>> {
  try {
    if (config.responseType === 'blob') {
      const blob = await service.request<Blob>(config)
      return parseBlobResponse<T>(blob.data, blob.headers['x-trace-id'])
    }

    const res = await service.request<ApiResponse<T>>(config)
    return parseApiResponse(res.data, res.headers['x-trace-id'])
  } catch (error) {
    return parseError<T>(error)
  }
}

function requestByMethod<T = unknown>(
  method: Method,
  url: string,
  payload?: unknown,
  config?: AxiosRequestConfig
) {
  if (method === 'GET') {
    return request<T>({ url, params: payload, method, ...config })
  }

  return request<T>({ url, data: payload, method, ...config })
}

const http = {
  get<T = unknown>(url: string, params?: unknown, config?: AxiosRequestConfig) {
    return requestByMethod<T>('GET', url, params, config)
  },
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return requestByMethod<T>('POST', url, data, config)
  },
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return requestByMethod<T>('PUT', url, data, config)
  },
  delete<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return requestByMethod<T>('DELETE', url, data, config)
  },
}

function handlePage<T>(res: HttpResult<PageResult<T>>): PageResult<T> {
  if (!res.ok || !res.data) return { list: [], total: 0 }
  return res.data
}

export { http, handlePage, service }
