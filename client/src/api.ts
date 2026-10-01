import type { User, Workshop } from './types'

const baseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
  }
}

function getCookie(name: string): string | undefined {
  return document.cookie.split('; ').find((entry) => entry.startsWith(`${name}=`))?.split('=').slice(1).join('=')
}

async function getCsrf(): Promise<void> {
  if (!getCookie('csrf_token')) {
    await fetch(`${baseUrl}/auth/csrf`, { credentials: 'include' })
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = init.method?.toUpperCase() ?? 'GET'
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) await getCsrf()
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  const csrf = getCookie('csrf_token')
  if (csrf && !['GET', 'HEAD', 'OPTIONS'].includes(method)) headers.set('X-CSRF-Token', csrf)
  const response = await fetch(`${baseUrl}${path}`, { ...init, headers, credentials: 'include' })
  const data: unknown = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof data === 'object' && data && 'detail' in data && typeof data.detail === 'string' ? data.detail : 'No fue posible completar la operación.'
    throw new ApiError(detail, response.status)
  }
  return data as T
}

export const api = {
  me: () => request<User>('/auth/me'),
  login: (email: string, password: string) => request<User>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (full_name: string, email: string, password: string, workshop_name: string) => request<User>('/auth/register', { method: 'POST', body: JSON.stringify({ full_name, email, password, workshop_name }) }),
  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),
  workshops: () => request<Workshop[]>('/workshops'),
  createWorkshop: (name: string, tax_id?: string) => request<Workshop>('/workshops', { method: 'POST', body: JSON.stringify({ name, tax_id: tax_id || null }) }),
  createCustomer: (workshopId: string, name: string, phone: string, email?: string) => request<{ message: string }>(`/workshops/${workshopId}/customers`, { method: 'POST', body: JSON.stringify({ name, phone, email: email || null }) }),
}
