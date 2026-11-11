<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import AuthPanel from '@/components/AuthPanel.vue'
import DashboardPanel from '@/components/DashboardPanel.vue'
import RoleCreationPanel from '@/components/RoleCreationPanel.vue'
import RoleAdministrationPanel from '@/components/RoleAdministrationPanel.vue'
import WorkshopManagementPanel from '@/components/WorkshopManagementPanel.vue'
import CustomerAdministrationPanel from '@/components/CustomerAdministrationPanel.vue'
import VehicleRegistrationPanel from '@/components/VehicleRegistrationPanel.vue'
import VehicleAdministrationPanel from '@/components/VehicleAdministrationPanel.vue'
import MyVehiclesPanel from '@/components/MyVehiclesPanel.vue'
import ToastMessage from '@/components/ToastMessage.vue'
import type { Customer, Notice, User } from '@/types'

const user = ref<User | null>(null)
const loading = ref(true)
const notice = ref<Notice | null>(null)
const isDark = ref(false)
const activeView = ref<'dashboard' | 'roles' | 'manage-roles' | 'workshops' | 'customers' | 'vehicles' | 'vehicle-admin' | 'my-vehicles'>('dashboard')
const vehicleCustomer = ref<Customer | null>(null)
const sidebarOpen = ref(false)
let noticeTimer: ReturnType<typeof setTimeout> | undefined

const canManageRoles = computed(() => user.value?.memberships.some((membership) => membership.role === 'admin' && membership.workshop_active) ?? false)
const canManageCustomers = computed(() => user.value?.memberships.some((membership) => ['admin', 'reception'].includes(membership.role) && membership.workshop_active) ?? false)
const canViewOwnVehicles = computed(() => user.value?.memberships.some((membership) => membership.role === 'customer' && membership.workshop_active) ?? false)

function showNotice(kind: Notice['kind'], text: string) {
  const durationMs = kind === 'error' ? 8000 : 5500
  notice.value = { kind, text, durationMs }
  if (noticeTimer) clearTimeout(noticeTimer)
  noticeTimer = setTimeout(clearNotice, durationMs)
}

function clearNotice() {
  notice.value = null
  if (noticeTimer) clearTimeout(noticeTimer)
  noticeTimer = undefined
}

function selectView(view: 'dashboard' | 'roles' | 'manage-roles' | 'workshops' | 'customers' | 'vehicle-admin' | 'my-vehicles') {
  if ((view === 'roles' || view === 'manage-roles' || view === 'workshops') && !canManageRoles.value) {
    showNotice('error', 'Solo un administrador puede acceder a la creación y asignación de roles.')
    return
  }
  if (view === 'customers' && !canManageCustomers.value) {
    showNotice('error', 'Solo un administrador o recepcionista puede administrar clientes.')
    return
  }
  if (view === 'vehicle-admin' && !canManageCustomers.value) {
    showNotice('error', 'Solo un administrador o recepcionista puede administrar vehículos.')
    return
  }
  if (view === 'my-vehicles' && !canViewOwnVehicles.value) {
    showNotice('error', 'Solo una cuenta de cliente autorizada puede consultar sus vehículos.')
    return
  }
  activeView.value = view
  sidebarOpen.value = false
}

function openVehicle(customer: Customer) {
  if (!canManageCustomers.value) {
    showNotice('error', 'Solo un administrador o recepcionista puede registrar vehículos.')
    return
  }
  vehicleCustomer.value = customer
  activeView.value = 'vehicles'
  sidebarOpen.value = false
}

async function logout() {
  try { await tallerMecanicoFacade.signOut() }
  catch (error) { showNotice('error', error instanceof Error ? error.message : 'No se pudo cerrar la sesión.') }
  finally {
    user.value = null
    activeView.value = 'dashboard'
    vehicleCustomer.value = null
  }
}

onMounted(async () => {
  isDark.value = window.localStorage.getItem('taller-theme') === 'dark'
  try { user.value = await tallerMecanicoFacade.getCurrentUser() }
  catch (error) { if (!tallerMecanicoFacade.isUnauthenticated(error)) showNotice('error', error instanceof Error ? error.message : 'No se pudo comprobar la sesión.') }
  finally { loading.value = false }
})

function toggleTheme() {
  isDark.value = !isDark.value
  window.localStorage.setItem('taller-theme', isDark.value ? 'dark' : 'light')
}
</script>

<template>
  <div class="app-root" :class="{ 'theme-dark': isDark }">
    <button class="theme-toggle" type="button" :aria-label="isDark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'" :title="isDark ? 'Tema claro' : 'Tema oscuro'" @click="toggleTheme"><span aria-hidden="true">{{ isDark ? '☀' : '☾' }}</span><span class="theme-toggle-label">{{ isDark ? 'Claro' : 'Oscuro' }}</span></button>
    <div v-if="loading" class="page-loader"><span></span><p>Preparando tu espacio de trabajo…</p></div>
  <div v-else-if="user" class="app-shell">
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false"></div>
    <aside class="app-sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-brand"><span class="brand-mark small">TM</span><span>Taller Mecánico</span></div>
      <p class="sidebar-label">NAVEGACIÓN</p>
      <nav class="sidebar-nav" aria-label="Navegación principal">
        <button class="nav-item" :class="{ active: activeView === 'dashboard' }" @click="selectView('dashboard')"><span>⌂</span> Inicio</button>
        <button v-if="canManageRoles" class="nav-item" :class="{ active: activeView === 'roles' }" @click="selectView('roles')"><span>♙</span> Crear y asignar roles</button>
        <button v-if="canManageRoles" class="nav-item" :class="{ active: activeView === 'manage-roles' }" @click="selectView('manage-roles')"><span>♧</span> Administrar roles</button>
        <button v-if="canManageRoles" class="nav-item" :class="{ active: activeView === 'workshops' }" @click="selectView('workshops')"><span>▣</span> Talleres</button>
        <button v-if="canManageCustomers" class="nav-item" :class="{ active: activeView === 'customers' || activeView === 'vehicles' }" @click="selectView('customers')"><span>♙</span> Clientes</button>
        <button v-if="canManageCustomers" class="nav-item" :class="{ active: activeView === 'vehicle-admin' }" @click="selectView('vehicle-admin')"><span>▤</span> Vehículos</button>
        <button v-if="canViewOwnVehicles" class="nav-item" :class="{ active: activeView === 'my-vehicles' }" @click="selectView('my-vehicles')"><span>▤</span> Mis vehículos</button>
      </nav>
      <div class="sidebar-footer"><span class="dot"></span><span>Sesión protegida</span></div>
    </aside>
    <div class="app-main">
      <header class="app-header"><button class="menu-toggle" aria-label="Abrir menú" @click="sidebarOpen = !sidebarOpen">☰</button><div class="header-context"><span class="eyebrow">ESPACIO DE TRABAJO</span><strong>{{ activeView === 'roles' ? 'Crear y asignar roles' : activeView === 'manage-roles' ? 'Administrar roles' : activeView === 'workshops' ? 'Talleres' : activeView === 'customers' ? 'Administración de clientes' : activeView === 'vehicle-admin' ? 'Administración de vehículos' : activeView === 'my-vehicles' ? 'Mis vehículos' : activeView === 'vehicles' ? 'Registrar vehículo' : 'Panel de control' }}</strong></div><div class="profile"><span>{{ user.full_name }}</span><button @click="logout">Cerrar sesión</button></div></header>
      <DashboardPanel v-if="activeView === 'dashboard'" :user="user" @notice="showNotice" />
      <RoleCreationPanel v-else-if="activeView === 'roles'" :user="user" @notice="showNotice" />
      <RoleAdministrationPanel v-else-if="activeView === 'manage-roles'" @notice="showNotice" />
      <WorkshopManagementPanel v-else-if="activeView === 'workshops'" @notice="showNotice" />
      <CustomerAdministrationPanel v-else-if="activeView === 'customers'" @notice="showNotice" @open-vehicle="openVehicle" />
      <VehicleAdministrationPanel v-else-if="activeView === 'vehicle-admin'" @notice="showNotice" />
      <MyVehiclesPanel v-else-if="activeView === 'my-vehicles'" @notice="showNotice" />
      <VehicleRegistrationPanel v-else-if="activeView === 'vehicles' && vehicleCustomer" :key="vehicleCustomer.id" :customer="vehicleCustomer" @notice="showNotice" @back="activeView = 'customers'" />
      <DashboardPanel v-else :user="user" @notice="showNotice" />
    </div>
  </div>
    <AuthPanel v-else @authenticated="user = $event" @notice="showNotice" />
    <ToastMessage :notice="notice" @dismiss="clearNotice" />
  </div>
</template>
