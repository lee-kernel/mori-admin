/**
 * 工具函数集合（TypeScript 版本）
 * 提供常用校验方法：URL、邮箱、大小写、数组、字符串等
 */

/**
 * 判断路径是否为外部链接
 * @param path - 待校验路径
 * @returns 是否为外部链接 (http, https, mailto, tel)
 */
export function isExternal(path: string): boolean {
  return /^(https?:|mailto:|tel:)/.test(path)
}

/**
 * 校验用户名是否合法
 * 仅允许 'admin' 或 'editor'
 * @param str - 用户名
 * @returns 是否有效
 */
export function validUsername(str: string): boolean {
  const valid_map = ['admin', 'editor']
  return valid_map.includes(str.trim())
}

/**
 * 校验 URL 格式是否正确
 * 支持 http(s)、ftp
 * @param url - 待校验 URL
 * @returns 是否有效
 */
export function validURL(url: string): boolean {
  const reg =
    /^(https?|ftp):\/\/([a-zA-Z0-9.-]+(:[a-zA-Z0-9.&%$-]+)*@)*((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}|([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(:[0-9]+)*(\/($|[a-zA-Z0-9.,?'\\+&%$#=~_-]+))*$/
  return reg.test(url)
}

/**
 * 校验是否全为小写字母
 * @param str - 待校验字符串
 * @returns 是否全小写
 */
export function validLowerCase(str: string): boolean {
  const reg = /^[a-z]+$/
  return reg.test(str)
}

/**
 * 校验是否全为大写字母
 * @param str - 待校验字符串
 * @returns 是否全大写
 */
export function validUpperCase(str: string): boolean {
  const reg = /^[A-Z]+$/
  return reg.test(str)
}

/**
 * 校验是否仅包含字母（大小写不限）
 * @param str - 待校验字符串
 * @returns 是否仅字母
 */
export function validAlphabets(str: string): boolean {
  const reg = /^[A-Za-z]+$/
  return reg.test(str)
}

/**
 * 校验邮箱格式
 * @param email - 待校验邮箱
 * @returns 是否符合邮箱格式
 */
export function validEmail(email: string): boolean {
  const reg =
    /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
  return reg.test(email)
}

/**
 * 判断是否为字符串
 * @param str - 待校验值
 * @returns 是否为字符串
 */
export function isString(str: unknown): str is string {
  return typeof str === 'string' || str instanceof String
}

/**
 * 判断是否为数组
 * @param arg - 待校验值
 * @returns 是否为数组
 */
export function isArray<T = any>(arg: unknown): arg is T[] {
  if (typeof Array.isArray === 'undefined') {
    return Object.prototype.toString.call(arg) === '[object Array]'
  }
  return Array.isArray(arg)
}

/**
 * 生成唯一 ID
 * @returns 唯一 ID 字符串
 */
export function generateUniqueId(): string {
  // 使用时间戳 + 随机数生成唯一ID
  return 'id_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 11)
}
