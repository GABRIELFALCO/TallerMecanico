import type { Customer, PostalCodeLookup, RoleAssignment, User, Vehicle, VehicleDetails, VehicleUpdateDetails, Workshop } from './types'

// En desarrollo usamos el proxy de Vite (`/api`) para mantener el frontend y
// la API en el mismo origen. Esto evita que el navegador bloquee las cookies
// de sesión/CSRF por diferencias entre localhost y 127.0.0.1.
const baseUrl = import.meta.env.VITE_API_URL ?? '/api'
const postalApiUrl = 'https://postali.app/api/v1/mx'

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
    const response = await fetch(`${baseUrl}/auth/csrf`, { credentials: 'include' })
    if (!response.ok) {
      throw new ApiError('No se pudo preparar la seguridad de la sesión. Reinicia el backend e inténtalo de nuevo.', response.status)
    }
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = init.method?.toUpperCase() ?? 'GET'
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) await getCsrf()
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  const csrf = getCookie('csrf_token')
  if (csrf && !['GET', 'HEAD', 'OPTIONS'].includes(method)) headers.set('X-CSRF-Token', csrf)
  let response: Response
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, headers, credentials: 'include' })
  } catch {
    throw new ApiError('No se pudo conectar con el servidor. Verifica que FastAPI esté ejecutándose en el puerto 8000.', 0)
  }
  const data: unknown = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof data === 'object' && data && 'detail' in data && typeof data.detail === 'string' ? data.detail : 'No fue posible completar la operación.'
    throw new ApiError(detail, response.status)
  }
  return data as T
}

async function lookupPostalCode(postalCode: string): Promise<PostalCodeLookup> {
  const response = await fetch(`${postalApiUrl}/cp/${encodeURIComponent(postalCode)}`)
  const data: unknown = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new ApiError('No encontramos ese código postal. Verifica los cinco dígitos.', response.status)
  }
  return data as PostalCodeLookup
}

export const api = {
  me: () => request<User>('/auth/me'),
  login: (email: string, password: string) => request<User>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (full_name: string, email: string, password: string, workshop_name: string, workshop_tax_id: string, workshop_state: string, workshop_municipality: string, workshop_locality: string, workshop_colony: string, workshop_postal_code: string) => request<User>('/auth/register', { method: 'POST', body: JSON.stringify({ full_name, email, password, workshop_name, workshop_tax_id, workshop_state, workshop_municipality, workshop_locality, workshop_colony, workshop_postal_code }) }),
  registerCustomerAccount: (full_name: string, email: string, password: string, workshop_tax_id: string) => request<User>('/auth/register-customer', { method: 'POST', body: JSON.stringify({ full_name, email, password, workshop_tax_id }) }),
  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),
  workshops: () => request<Workshop[]>('/workshops'),
  createWorkshop: (name: string, tax_id: string, address: { state: string; municipality: string; locality: string; colony: string; postal_code: string }, photoDataUrl?: string) => request<Workshop>('/workshops', { method: 'POST', body: JSON.stringify({ name, tax_id, ...address, photo_data_url: photoDataUrl ?? null }) }),
  adminWorkshops: () => request<Workshop[]>('/admin/workshops'),
  updateWorkshop: (workshopId: string, name: string, tax_id: string, address: { state: string; municipality: string; locality: string; colony: string; postal_code: string }) => request<Workshop>(`/admin/workshops/${workshopId}`, { method: 'PATCH', body: JSON.stringify({ name, tax_id, ...address }) }),
  updateWorkshopStatus: (workshopId: string, isActive: boolean) => request<{ message: string }>(`/admin/workshops/${workshopId}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) }),
  assignRole: (workshopId: string, email: string, role: string) => request<{ message: string }>(`/workshops/${workshopId}/members`, { method: 'POST', body: JSON.stringify({ email, role }) }),
  roleAssignments: (workshopId: string) => request<RoleAssignment[]>(`/workshops/${workshopId}/role-assignments`),
  updateRole: (workshopId: string, membershipId: string, role: string) => request<{ message: string }>(`/workshops/${workshopId}/members/${membershipId}/role`, { method: 'PATCH', body: JSON.stringify({ role }) }),
  updateMemberStatus: (workshopId: string, membershipId: string, isActive: boolean) => request<{ message: string }>(`/workshops/${workshopId}/members/${membershipId}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) }),
  createCustomer: (workshopId: string, full_name: string, phone: string, email: string) => request<{ message: string }>(`/workshops/${workshopId}/customers`, { method: 'POST', body: JSON.stringify({ full_name, phone, email, confirm_registration: true }) }),
  customers: (workshopId: string) => request<Customer[]>(`/workshops/${workshopId}/customers`),
  updateCustomer: (workshopId: string, customerId: string, full_name: string, phone: string, email: string) => request<Customer>(`/workshops/${workshopId}/customers/${customerId}`, { method: 'PATCH', body: JSON.stringify({ full_name, phone, email, confirm_update: true }) }),
  updateCustomerStatus: (workshopId: string, customerId: string, isActive: boolean) => request<{ message: string; is_active: boolean }>(`/workshops/${workshopId}/customers/${customerId}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) }),
  vehicles: (workshopId: string, customerId: string) => request<Vehicle[]>(`/workshops/${workshopId}/customers/${customerId}/vehicles`),
  createVehicle: (workshopId: string, customerId: string, vehicle: VehicleDetails, photoDataUrl?: string) => request<Vehicle>(`/workshops/${workshopId}/customers/${customerId}/vehicles`, { method: 'POST', body: JSON.stringify({ ...vehicle, photo_data_url: photoDataUrl ?? null }) }),
  workshopVehicles: (workshopId: string) => request<Vehicle[]>(`/workshops/${workshopId}/vehicles`),
  updateVehicle: (workshopId: string, vehicleId: string, vehicle: VehicleUpdateDetails) => request<Vehicle>(`/workshops/${workshopId}/vehicles/${vehicleId}`, { method: 'PATCH', body: JSON.stringify({ ...vehicle, confirm_update: true }) }),
  updateVehicleStatus: (workshopId: string, vehicleId: string, isActive: boolean) => request<{ message: string; is_active: boolean }>(`/workshops/${workshopId}/vehicles/${vehicleId}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) }),
  myVehicles: (workshopId: string) => request<Vehicle[]>(`/workshops/${workshopId}/my-vehicles`),
  lookupPostalCode,
}
