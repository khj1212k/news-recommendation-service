import { getToken } from './storage'

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
const DEFAULT_ERROR = '요청에 실패했습니다'

function extractErrorMessage(payload: any): string {
  if (!payload) {
    return DEFAULT_ERROR
  }
  const detail = payload.detail ?? payload
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item) {
          return ''
        }
        if (typeof item === 'string') {
          return item
        }
        if (item.msg) {
          return item.msg
        }
        return ''
      })
      .filter(Boolean)
    if (messages.length > 0) {
      return messages.join(' / ')
    }
  }
  if (typeof detail === 'object' && detail.msg) {
    return detail.msg
  }
  return DEFAULT_ERROR
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {})
  headers.set('Content-Type', 'application/json')
  const token = getToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(extractErrorMessage(detail))
  }
  return response.json()
}

export async function publicFetch(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {})
  headers.set('Content-Type', 'application/json')
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(extractErrorMessage(detail))
  }
  return response.json()
}
