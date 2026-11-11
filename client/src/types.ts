export type Role = 'admin' | 'reception' | 'service_advisor' | 'technician' | 'customer' | 'system'

export interface Membership {
  workshop_id: string
  workshop_name: string
  workshop_active: boolean
  role: Role
}

export interface User {
  id: string
  full_name: string
  email: string
  is_verified: boolean
  memberships: Membership[]
}

export interface Workshop {
  id: string
  name: string
  tax_id: string | null
  state: string | null
  municipality: string | null
  locality: string | null
  colony: string | null
  postal_code: string | null
  photo_url?: string | null
  is_active: boolean
  role: Role
}

export type WorkshopSnapshot = Omit<Workshop, 'role'> & { role?: Role }

export interface Customer {
  id: string
  full_name: string
  phone: string
  email: string
  is_active: boolean
  workshop: WorkshopSnapshot
  message?: string
}

export interface Vehicle {
  id: string
  system_vin: string
  workshop_id: string
  customer_id: string
  vin: string
  plate: string
  brand: string
  model: string
  year: number
  version: string
  color: string
  mileage: number | null
  technician_id: string | null
  is_active: boolean
  photo_url?: string | null
  customer_name?: string | null
  customer_email?: string | null
  customer_phone?: string | null
  customer_is_active?: boolean
  message?: string
}

export type VehicleDetails = Pick<Vehicle, 'vin' | 'plate' | 'brand' | 'model' | 'year' | 'version' | 'color' | 'mileage'>
export type VehicleUpdateDetails = Omit<VehicleDetails, 'vin' | 'mileage'> & { mileage: number }

export interface WorkshopAddress {
  state: string
  municipality: string
  locality: string
  colony: string
  postal_code: string
}

export interface PostalSettlement {
  nombre: string
  tipo: string
  ciudad: string
  zona?: string
}

export interface PostalCodeLookup {
  cp: string
  estado: string
  municipio: string
  asentamientos: PostalSettlement[]
}

export interface RoleAssignment {
  membership_id: string
  user_id: string
  full_name: string
  email: string
  role: Role
  role_name: string
  is_active: boolean
  user_active: boolean
}

export interface Notice {
  kind: 'success' | 'error'
  text: string
  durationMs?: number
}

export interface ConfirmationRequest {
  title: string
  message: string
  confirmLabel: string
  variant: 'standard' | 'danger'
}
