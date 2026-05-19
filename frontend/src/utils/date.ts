/**
 * 日期格式化工具函数
 * 统一处理时区转换，确保服务器返回的UTC时间正确显示为UTC+8
 */

/**
 * 格式化日期时间为UTC+8时区字符串（完整格式）
 * @param dateStr - 日期字符串（可为 null）
 * @returns 格式化后的日期时间字符串，如 "2026-05-19 19:55:23"
 */
export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  // 确保字符串被解析为 UTC 时间（追加 'Z'）
  const utcDate = new Date(dateStr + (dateStr.includes('Z') || dateStr.includes('+') || (dateStr.includes('-') && dateStr.slice(-5).includes(':')) ? '' : 'Z'))
  return utcDate.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

/**
 * 格式化日期为UTC+8时区字符串（仅日期）
 * @param dateStr - 日期字符串
 * @returns 格式化后的日期字符串，如 "2026/5/19"
 */
export function formatDateOnly(dateStr: string): string {
  const utcDate = new Date(dateStr + (dateStr.includes('Z') || dateStr.includes('+') || (dateStr.includes('-') && dateStr.slice(-5).includes(':')) ? '' : 'Z'))
  return utcDate.toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

/**
 * 格式化日期时间为UTC+8时区字符串（仅时间）
 * @param dateStr - 日期字符串
 * @returns 格式化后的时间字符串，如 "19:55:23"
 */
export function formatTimeOnly(dateStr: string): string {
  const utcDate = new Date(dateStr + (dateStr.includes('Z') || dateStr.includes('+') || (dateStr.includes('-') && dateStr.slice(-5).includes(':')) ? '' : 'Z'))
  return utcDate.toLocaleTimeString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

/**
 * 格式化相对时间（如"2分钟前"、"1小时前"）
 * @param dateStr - 日期字符串
 * @returns 相对时间字符串
 */
export function formatRelativeTime(dateStr: string): string {
  const utcDate = new Date(dateStr + (dateStr.includes('Z') || dateStr.includes('+') || (dateStr.includes('-') && dateStr.slice(-5).includes(':')) ? '' : 'Z'))
  const now = new Date()
  const diffMs = now.getTime() - utcDate.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSecs < 60) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return formatDate(dateStr)
}