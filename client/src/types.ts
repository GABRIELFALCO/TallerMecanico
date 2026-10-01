export type Role = 'owner' | 'manager' | 'reception' | 'mechanic'

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
  is_active: boolean
  role: Role
}

export interface Notice {
  kind: 'success' | 'error'
  text: string
}
