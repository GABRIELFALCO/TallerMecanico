<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import ConfirmationDialog from '@/components/ConfirmationDialog.vue'
import type { ConfirmationRequest, Role, RoleAssignment, Workshop } from '@/types'

type PendingConfirmation = { kind: 'role'; item: RoleAssignment; role: Role } | { kind: 'status'; item: RoleAssignment }

const emit = defineEmits<{ notice: [kind: 'success' | 'error', text: string] }>()

const workshops = ref<Workshop[]>([])
const assignments = ref<RoleAssignment[]>([])
const selectedId = ref('')
const editingId = ref<string | null>(null)
const editingRole = ref<Role>('reception')
const busyId = ref<string | null>(null)
const confirmation = ref<ConfirmationRequest | null>(null)
const pendingConfirmation = ref<PendingConfirmation | null>(null)
const confirmationBusy = ref(false)

const roleNames: Record<Role, string> = {
  admin: 'Administrador',
  reception: 'Recepcionista',
  service_advisor: 'Asesor de servicio',
  technician: 'Técnico',
  customer: 'Cliente',
  system: 'Sistema',
}
const roleOptions = Object.entries(roleNames) as [Role, string][]
const adminWorkshops = computed(() => workshops.value.filter((workshop) => workshop.role === 'admin' && workshop.is_active))
const selectedWorkshop = computed(() => adminWorkshops.value.find((workshop) => workshop.id === selectedId.value))
const activeCount = computed(() => assignments.value.filter((item) => item.is_active).length)
const disabledCount = computed(() => assignments.value.filter((item) => !item.is_active).length)
const rolesInUse = computed(() => new Set(assignments.value.map((item) => item.role)).size)

async function loadAssignments() {
  if (!selectedId.value) {
    assignments.value = []
    return
  }
  try {
    assignments.value = await tallerMecanicoFacade.listRoleAssignments(selectedId.value)
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar las asignaciones.') }
}

async function loadWorkshops() {
  try {
    workshops.value = await tallerMecanicoFacade.listWorkshops()
    selectedId.value = adminWorkshops.value[0]?.id ?? ''
    if (!selectedId.value) emit('notice', 'error', 'No tienes un taller activo con rol de administrador.')
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los talleres.') }
}

function roleLabel(role: Role): string { return roleNames[role] }

function beginEdit(item: RoleAssignment) {
  editingId.value = item.membership_id
  editingRole.value = item.role
}

function cancelEdit() { editingId.value = null }

function saveRole(item: RoleAssignment) {
  if (editingRole.value === item.role) {
    editingId.value = null
    return
  }
  pendingConfirmation.value = { kind: 'role', item, role: editingRole.value }
  confirmation.value = {
    title: 'Actualizar rol del usuario',
    message: `Se cambiará el rol de ${item.full_name} de ${roleLabel(item.role)} a ${roleLabel(editingRole.value)} en ${selectedWorkshop.value?.name ?? 'este taller'}.`,
    confirmLabel: 'Actualizar rol',
    variant: 'standard',
  }
}

async function persistRole(item: RoleAssignment, role: Role) {
  busyId.value = item.membership_id
  try {
    const result = await tallerMecanicoFacade.updateRole(selectedId.value, item.membership_id, role)
    editingId.value = null
    emit('notice', 'success', result.message)
    await loadAssignments()
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo actualizar el rol.') } finally { busyId.value = null }
}

function toggleStatus(item: RoleAssignment) {
  pendingConfirmation.value = { kind: 'status', item }
  confirmation.value = {
    title: item.is_active ? 'Deshabilitar acceso' : 'Reactivar acceso',
    message: item.is_active
      ? `Se bloqueará el acceso de ${item.full_name} a ${selectedWorkshop.value?.name ?? 'este taller'}. El historial de su asignación se conservará.`
      : `Se volverá a habilitar el acceso de ${item.full_name} a ${selectedWorkshop.value?.name ?? 'este taller'}.`,
    confirmLabel: item.is_active ? 'Deshabilitar acceso' : 'Reactivar acceso',
    variant: item.is_active ? 'danger' : 'standard',
  }
}

async function persistStatus(item: RoleAssignment) {
  busyId.value = item.membership_id
  try {
    const result = await tallerMecanicoFacade.updateMemberStatus(selectedId.value, item.membership_id, !item.is_active)
    emit('notice', 'success', result.message)
    await loadAssignments()
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo actualizar el estado.') } finally { busyId.value = null }
}

async function confirmPendingAction() {
  const action = pendingConfirmation.value
  if (!action || confirmationBusy.value) return
  confirmationBusy.value = true
  try {
    if (action.kind === 'role') await persistRole(action.item, action.role)
    else await persistStatus(action.item)
  } finally {
    confirmationBusy.value = false
    confirmation.value = null
    pendingConfirmation.value = null
  }
}

function cancelPendingAction() {
  if (confirmationBusy.value) return
  confirmation.value = null
  pendingConfirmation.value = null
}

watch(selectedId, loadAssignments)
onMounted(loadWorkshops)
</script>

<template>
  <main class="dashboard roles-page">
    <section class="dashboard-title roles-heading"><p class="eyebrow">CONTROL DE ACCESOS</p><h1>Administrar roles.</h1><p>Consulta y actualiza quién tiene acceso a cada taller. Las cuentas se deshabilitan, nunca se eliminan.</p></section>
    <section class="admin-toolbar"><label>Taller administrado<select v-model="selectedId" :disabled="!adminWorkshops.length"><option value="" disabled>Selecciona un taller</option><option v-for="workshop in adminWorkshops" :key="workshop.id" :value="workshop.id">{{ workshop.name }}</option></select></label><div v-if="selectedWorkshop" class="selected-workshop"><span class="dot"></span><span>{{ selectedWorkshop.name }}</span><small>Administrador autorizado</small></div></section>
    <section class="role-summary">
      <article class="role-stat"><span class="stat-icon">♙</span><div><strong>{{ roleOptions.length }}</strong><span>roles disponibles</span></div></article>
      <article class="role-stat"><span class="stat-icon green">✓</span><div><strong>{{ activeCount }}</strong><span>asignaciones activas</span></div></article>
      <article class="role-stat"><span class="stat-icon gold">!</span><div><strong>{{ disabledCount }}</strong><span>deshabilitadas · {{ rolesInUse }} roles en uso</span></div></article>
    </section>
    <section class="form-card role-table-card">
      <div class="table-heading"><div><p class="eyebrow">ASIGNACIONES DEL TALLER</p><h2>Usuarios y permisos</h2></div><span class="table-count">{{ assignments.length }} registros</span></div>
      <div v-if="assignments.length" class="role-table-wrap">
        <table class="role-table"><thead><tr><th>Usuario</th><th>Rol</th><th>Estado</th><th>Actualizaciones</th><th>Acciones</th></tr></thead><tbody><tr v-for="item in assignments" :key="item.membership_id" :class="{ inactive: !item.is_active }"><td><strong>{{ item.full_name }}</strong><small>{{ item.email }}</small></td><td><template v-if="editingId === item.membership_id"><select v-model="editingRole"><option v-for="role in roleOptions" :key="role[0]" :value="role[0]">{{ role[1] }}</option></select></template><span v-else class="role-pill">{{ roleLabel(item.role) }}</span></td><td><span class="status-pill" :class="item.is_active ? 'active' : 'disabled'"><span class="status-dot"></span>{{ item.is_active ? 'Activo' : 'Deshabilitado' }}</span></td><td><span class="update-copy">{{ item.is_active ? 'Acceso vigente' : 'Acceso bloqueado' }}</span></td><td class="action-cell"><template v-if="editingId === item.membership_id"><button class="table-action confirm" :disabled="busyId === item.membership_id" @click="saveRole(item)">{{ busyId === item.membership_id ? 'Guardando…' : 'Guardar' }}</button><button class="table-action" @click="cancelEdit">Cancelar</button></template><template v-else><button class="table-action" :disabled="busyId === item.membership_id" @click="beginEdit(item)">Editar</button><button class="table-action" :class="item.is_active ? 'danger' : 'confirm'" :disabled="busyId === item.membership_id" @click="toggleStatus(item)">{{ item.is_active ? 'Deshabilitar' : 'Reactivar' }}</button></template></td></tr></tbody></table>
      </div>
      <div v-else class="empty-state table-empty">Selecciona un taller administrable para consultar sus asignaciones.</div>
      <p class="no-delete-note"><span>⌁</span> Las asignaciones no se eliminan físicamente. Al deshabilitarlas se conserva el historial y se bloquea el acceso al taller.</p>
    </section>
    <ConfirmationDialog :request="confirmation" :busy="confirmationBusy" @confirm="confirmPendingAction" @cancel="cancelPendingAction" />
  </main>
</template>
