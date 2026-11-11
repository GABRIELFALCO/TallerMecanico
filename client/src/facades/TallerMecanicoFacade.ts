import { api as backendApi, ApiError } from '@/api'
import type { Customer, PostalCodeLookup, RoleAssignment, User, Vehicle, VehicleDetails, VehicleUpdateDetails, Workshop, WorkshopAddress } from '@/types'

export interface CustomerRegistration {
  fullName: string
  phone: string
  email: string
}

/**
 * Facade del cliente web.
 *
 * Los componentes no conocen fetch, cookies, CSRF ni las rutas HTTP. Todas
 * las entradas al subsistema remoto pasan por esta fachada única.
 */
export class TallerMecanicoFacade {
  isUnauthenticated(error: unknown): boolean {
    return error instanceof ApiError && error.status === 401
  }

  getCurrentUser(): Promise<User> {
    return backendApi.me()
  }

  signIn(email: string, password: string): Promise<User> {
    return backendApi.login(email, password)
  }

  createAccount(fullName: string, email: string, password: string, workshopName: string, workshopTaxId: string, address: WorkshopAddress): Promise<User> {
    return backendApi.register(fullName, email, password, workshopName, workshopTaxId, address.state, address.municipality, address.locality, address.colony, address.postal_code)
  }

  createCustomerAccount(fullName: string, email: string, password: string, workshopTaxId: string): Promise<User> {
    return backendApi.registerCustomerAccount(fullName, email, password, workshopTaxId)
  }

  signOut(): Promise<{ message: string }> {
    return backendApi.logout()
  }

  listWorkshops(): Promise<Workshop[]> {
    return backendApi.workshops()
  }

  createWorkshop(name: string, taxId: string, address: WorkshopAddress, photoDataUrl?: string): Promise<Workshop> {
    return backendApi.createWorkshop(name, taxId, address, photoDataUrl)
  }

  listAdminWorkshops(): Promise<Workshop[]> {
    return backendApi.adminWorkshops()
  }

  updateWorkshop(workshopId: string, name: string, taxId: string, address: WorkshopAddress): Promise<Workshop> {
    return backendApi.updateWorkshop(workshopId, name, taxId, address)
  }

  updateWorkshopStatus(workshopId: string, isActive: boolean): Promise<{ message: string }> {
    return backendApi.updateWorkshopStatus(workshopId, isActive)
  }

  assignRole(workshopId: string, email: string, role: string): Promise<{ message: string }> {
    return backendApi.assignRole(workshopId, email, role)
  }

  listRoleAssignments(workshopId: string): Promise<RoleAssignment[]> {
    return backendApi.roleAssignments(workshopId)
  }

  updateRole(workshopId: string, membershipId: string, role: string): Promise<{ message: string }> {
    return backendApi.updateRole(workshopId, membershipId, role)
  }

  updateMemberStatus(workshopId: string, membershipId: string, isActive: boolean): Promise<{ message: string }> {
    return backendApi.updateMemberStatus(workshopId, membershipId, isActive)
  }

  registerCustomer(workshopId: string, registration: CustomerRegistration): Promise<{ message: string }> {
    return backendApi.createCustomer(workshopId, registration.fullName, registration.phone, registration.email)
  }

  listCustomers(workshopId: string): Promise<Customer[]> {
    return backendApi.customers(workshopId)
  }

  updateCustomer(workshopId: string, customerId: string, fullName: string, phone: string, email: string): Promise<Customer> {
    return backendApi.updateCustomer(workshopId, customerId, fullName, phone, email)
  }

  updateCustomerStatus(workshopId: string, customerId: string, isActive: boolean): Promise<{ message: string; is_active: boolean }> {
    return backendApi.updateCustomerStatus(workshopId, customerId, isActive)
  }

  listVehicles(workshopId: string, customerId: string): Promise<Vehicle[]> {
    return backendApi.vehicles(workshopId, customerId)
  }

  registerVehicle(workshopId: string, customerId: string, vehicle: VehicleDetails, photoDataUrl?: string): Promise<Vehicle> {
    return backendApi.createVehicle(workshopId, customerId, vehicle, photoDataUrl)
  }

  listWorkshopVehicles(workshopId: string): Promise<Vehicle[]> {
    return backendApi.workshopVehicles(workshopId)
  }

  updateVehicle(workshopId: string, vehicleId: string, vehicle: VehicleUpdateDetails): Promise<Vehicle> {
    return backendApi.updateVehicle(workshopId, vehicleId, vehicle)
  }

  updateVehicleStatus(workshopId: string, vehicleId: string, isActive: boolean): Promise<{ message: string; is_active: boolean }> {
    return backendApi.updateVehicleStatus(workshopId, vehicleId, isActive)
  }

  listMyVehicles(workshopId: string): Promise<Vehicle[]> {
    return backendApi.myVehicles(workshopId)
  }

  lookupPostalCode(postalCode: string): Promise<PostalCodeLookup> {
    return backendApi.lookupPostalCode(postalCode)
  }
}

export const tallerMecanicoFacade = new TallerMecanicoFacade()
