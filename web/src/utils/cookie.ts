export const CookieUtil = {
  // 获取指定 cookie
  get(name: string): string | null {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
    return match ? decodeURIComponent(match[2]!) : null
  },

  // 设置 cookie
  set(
    name: string,
    value: string,
    days?: number,
    path = '/',
    sameSite: 'Strict' | 'Lax' | 'None' = 'Lax'
  ) {
    let expires = ''
    if (days) {
      const date = new Date()
      date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000)
      expires = '; expires=' + date.toUTCString()
    }

    const secure = window.location.protocol === 'https:' ? '; Secure' : ''
    document.cookie = `${name}=${encodeURIComponent(value)}${expires}; path=${path}; SameSite=${sameSite}${secure}`
  },

  // 删除 cookie
  remove(name: string, path = '/') {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=${path}`
  },
}
