const HAS_TIMEZONE = /(?:Z|[+-]\d{2}:?\d{2})$/i

/** 解析 API 时间戳；兼容旧接口中未携带时区但实际表示 UTC 的值。 */
export function parseTimestamp(value?: string | null): Date | null {
  if (!value) return null
  const normalized = HAS_TIMEZONE.test(value) ? value : `${value}Z`
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatParts(date: Date, options: Intl.DateTimeFormatOptions, separator = '-'): string {
  const parts = new Intl.DateTimeFormat('zh-CN', {
    hourCycle: 'h23',
    ...options,
  }).formatToParts(date)
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  const dateText = [values.year, values.month, values.day].filter(Boolean).join(separator)
  const timeText = [values.hour, values.minute, values.second].filter(Boolean).join(':')
  return [dateText, timeText].filter(Boolean).join(' ')
}

/** 将 API 的 UTC 时间戳按浏览器本地时区显示。 */
export function formatTimestamp(value?: string | null, fallback = '-'): string {
  const date = parseTimestamp(value)
  if (!date) return fallback
  return formatParts(date, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/** 将 API 时间戳显示为不含秒的本地时间。 */
export function formatTimestampShort(value?: string | null, fallback = '-'): string {
  const date = parseTimestamp(value)
  if (!date) return fallback
  return formatParts(date, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** 将 API 时间戳显示为月日，用于紧凑列表。 */
export function formatTimestampMonthDay(value?: string | null, fallback = '-'): string {
  const date = parseTimestamp(value)
  if (!date) return fallback
  return formatParts(date, { month: '2-digit', day: '2-digit' }, '/')
}

/** 格式化 APP_TIMEZONE 下的调度墙上时间，不执行浏览器时区转换。 */
export function formatWallDateTime(value?: string | null, fallback = '-'): string {
  return value ? value.replace('T', ' ').slice(0, 16) : fallback
}

/** 将日期时间选择器产生的浏览器本地时间转换为带时区的 UTC ISO 8601 字符串。 */
export function localDateTimeToUtcIso(value?: string | null): string | undefined {
  if (!value) return undefined
  const date = new Date(value.replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return value
  return date.toISOString()
}
