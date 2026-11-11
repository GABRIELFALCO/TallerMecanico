<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import ConfirmationDialog from '@/components/ConfirmationDialog.vue'
import type { ConfirmationRequest, Vehicle, VehicleUpdateDetails, Workshop } from '@/types'

type PendingConfirmation = { kind: 'save' } | { kind: 'status'; vehicle: Vehicle }

const emit = defineEmits<{ notice: [kind: 'success' | 'error', text: string] }>()
const workshops = ref<Workshop[]>([])
const vehicles = ref<Vehicle[]>([])
const selectedWorkshopId = ref('')
const search = ref('')
const loading = ref(false)
const busy = ref(false)
const busyId = ref<string | null>(null)
const editing = ref<Vehicle | null>(null)
const previewing = ref<Vehicle | null>(null)
const confirmation = ref<ConfirmationRequest | null>(null)
const pendingConfirmation = ref<PendingConfirmation | null>(null)
const confirmationBusy = ref(false)
const formError = ref('')
const yearMax = new Date().getFullYear() + 1
const platePattern = /^[A-Z0-9-]{4,10}$/
const editForm = reactive<Omit<VehicleUpdateDetails, 'mileage'> & { mileage: number | null }>({
  plate: '',
  brand: '',
  model: '',
  year: yearMax,
  version: '',
  color: '',
  mileage: null,
})

const selectedWorkshop = computed(() => workshops.value.find((item) => item.id === selectedWorkshopId.value))
const activeVehicles = computed(() => vehicles.value.filter((item) => item.is_active).length)
const disabledVehicles = computed(() => vehicles.value.filter((item) => !item.is_active).length)
const filteredVehicles = computed(() => {
  const needle = search.value.trim().toLowerCase()
  if (!needle) return vehicles.value
  return vehicles.value.filter((vehicle) => [vehicle.customer_name ?? '', vehicle.vin, vehicle.system_vin, vehicle.plate, vehicle.brand, vehicle.model].some((value) => value.toLowerCase().includes(needle)))
})

async function loadWorkshops() {
  try {
    workshops.value = await tallerMecanicoFacade.listWorkshops()
    selectedWorkshopId.value = workshops.value.find((item) => item.is_active && ['admin', 'reception'].includes(item.role))?.id ?? ''
    await loadVehicles()
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los talleres.') }
}

async function loadVehicles() {
  if (!selectedWorkshopId.value || !selectedWorkshop.value?.is_active) { vehicles.value = []; return }
  loading.value = true
  try { vehicles.value = await tallerMecanicoFacade.listWorkshopVehicles(selectedWorkshopId.value) }
  catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los vehículos.') }
  finally { loading.value = false }
}

function openEdit(vehicle: Vehicle) {
  previewing.value = null
  editing.value = vehicle
  formError.value = ''
  Object.assign(editForm, {
    plate: vehicle.plate,
    brand: vehicle.brand,
    model: vehicle.model,
    year: vehicle.year,
    version: vehicle.version,
    color: vehicle.color,
    mileage: vehicle.mileage,
  })
}

function openPreview(vehicle: Vehicle) {
  editing.value = null
  previewing.value = vehicle
}

function closePreview() {
  previewing.value = null
}

function closeEdit() {
  if (!busy.value) editing.value = null
}

function validateEdit(): boolean {
  editForm.plate = editForm.plate.trim().toUpperCase().replace(/\s+/g, '')
  editForm.brand = editForm.brand.trim()
  editForm.model = editForm.model.trim()
  editForm.version = editForm.version.trim()
  editForm.color = editForm.color.trim()
  if (!editForm.plate || !editForm.brand || !editForm.model || !editForm.version || !editForm.color) {
    formError.value = 'Completa todos los datos principales del vehículo.'
    return false
  }
  if (!platePattern.test(editForm.plate)) {
    formError.value = 'La placa debe tener entre 4 y 10 caracteres alfanuméricos.'
    return false
  }
  if (!Number.isInteger(editForm.year) || editForm.year < 1886 || editForm.year > yearMax) {
    formError.value = `El año debe estar entre 1886 y ${yearMax}.`
    return false
  }
  if (editForm.mileage === null || !Number.isInteger(editForm.mileage) || editForm.mileage < 0) {
    formError.value = 'Completa el kilometraje con un entero mayor o igual a cero.'
    return false
  }
  formError.value = ''
  return true
}

function saveEdit() {
  if (!editing.value || !selectedWorkshopId.value || !validateEdit()) return
  pendingConfirmation.value = { kind: 'save' }
  confirmation.value = {
    title: 'Guardar cambios del vehículo',
    message: `Se actualizarán los datos principales del vehículo ${editing.value.system_vin}. El VIN del automóvil permanecerá sin cambios.`,
    confirmLabel: 'Guardar cambios',
    variant: 'standard',
  }
}

async function persistEdit() {
  if (!editing.value || !selectedWorkshopId.value) return
  busy.value = true
  try {
    const payload: VehicleUpdateDetails = { ...editForm, mileage: editForm.mileage as number }
    const updated = await tallerMecanicoFacade.updateVehicle(selectedWorkshopId.value, editing.value.id, payload)
    const index = vehicles.value.findIndex((vehicle) => vehicle.id === updated.id)
    if (index >= 0) vehicles.value[index] = updated
    editing.value = null
    emit('notice', 'success', updated.message ?? 'Vehículo actualizado correctamente.')
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo actualizar el vehículo.') }
  finally { busy.value = false }
}

function toggleStatus(vehicle: Vehicle) {
  if (!selectedWorkshopId.value) return
  const action = vehicle.is_active ? 'deshabilitar' : 'reactivar'
  pendingConfirmation.value = { kind: 'status', vehicle }
  confirmation.value = {
    title: vehicle.is_active ? 'Deshabilitar vehículo' : 'Reactivar vehículo',
    message: vehicle.is_active
      ? `El vehículo con placa ${vehicle.plate} se deshabilitará, pero su historial se conservará.`
      : `El vehículo con placa ${vehicle.plate} volverá a estar disponible en el taller.`,
    confirmLabel: `${action[0].toUpperCase()}${action.slice(1)} vehículo`,
    variant: vehicle.is_active ? 'danger' : 'standard',
  }
}

async function persistStatus(vehicle: Vehicle) {
  if (!selectedWorkshopId.value) return
  busyId.value = vehicle.id
  try {
    const result = await tallerMecanicoFacade.updateVehicleStatus(selectedWorkshopId.value, vehicle.id, !vehicle.is_active)
    vehicle.is_active = result.is_active
    emit('notice', 'success', result.message)
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo actualizar el vehículo.') }
  finally { busyId.value = null }
}

async function confirmPendingAction() {
  const action = pendingConfirmation.value
  if (!action || confirmationBusy.value) return
  confirmationBusy.value = true
  try {
    if (action.kind === 'save') await persistEdit()
    else await persistStatus(action.vehicle)
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

watch(selectedWorkshopId, loadVehicles)
onMounted(loadWorkshops)
</script>

<template>
  <main class="dashboard roles-page vehicle-admin-page">
    <section class="dashboard-title roles-heading"><p class="eyebrow">OPERACIÓN DEL TALLER</p><h1>Administración de vehículos.</h1><p>Consulta los automóviles registrados y conserva su historial por cliente.</p></section>
    <section class="role-summary"><article class="role-stat"><span class="stat-icon">▣</span><div><strong>{{ vehicles.length }}</strong><span>vehículos registrados</span></div></article><article class="role-stat"><span class="stat-icon green">✓</span><div><strong>{{ activeVehicles }}</strong><span>vehículos activos</span></div></article><article class="role-stat"><span class="stat-icon gold">!</span><div><strong>{{ disabledVehicles }}</strong><span>deshabilitados</span></div></article></section>
    <section class="customer-toolbar form-card"><label>Taller de trabajo<select v-model="selectedWorkshopId"><option value="" disabled>Selecciona un taller activo</option><option v-for="workshop in workshops.filter((item) => ['admin', 'reception'].includes(item.role))" :key="workshop.id" :value="workshop.id">{{ workshop.name }} · {{ workshop.is_active ? 'Activo' : 'Inactivo' }}</option></select></label><label>Buscar vehículo<input v-model.trim="search" type="search" placeholder="Cliente, VIN, placa, marca o modelo" /></label><span v-if="selectedWorkshop" class="selected-workshop">{{ selectedWorkshop.name }} · {{ selectedWorkshop.is_active ? 'Activo' : 'Inactivo' }}</span></section>
    <section class="form-card role-table-card"><div class="table-heading"><div><p class="eyebrow">REGISTROS DEL TALLER</p><h2>Vehículos</h2></div><span class="table-count">{{ filteredVehicles.length }} resultados</span></div><div v-if="loading" class="empty-state table-empty">Cargando vehículos…</div><div v-else-if="!selectedWorkshop" class="empty-state table-empty">Selecciona un taller activo para consultar sus vehículos.</div><div v-else-if="filteredVehicles.length" class="role-table-wrap"><table class="role-table vehicle-admin-table"><thead><tr><th>Cliente</th><th>Vehículo</th><th>Identificación</th><th>Estado</th><th>Acciones</th></tr></thead><tbody><tr v-for="vehicle in filteredVehicles" :key="vehicle.id" :class="{ inactive: !vehicle.is_active }"><td><strong>{{ vehicle.customer_name || 'Cliente no disponible' }}</strong><small>{{ vehicle.customer_email || 'Sin correo' }}</small></td><td><div class="vehicle-photo-cell"><img v-if="vehicle.photo_url" class="vehicle-photo-thumb" :src="vehicle.photo_url" :alt="`Foto de ${vehicle.brand} ${vehicle.model}`" /><span v-else class="vehicle-photo-empty">Sin foto</span><div class="vehicle-photo-copy"><strong>{{ vehicle.brand }} {{ vehicle.model }}</strong><small>{{ vehicle.year }} · {{ vehicle.version }} · {{ vehicle.color }}</small></div></div></td><td><strong>{{ vehicle.system_vin }}</strong><small>VIN: {{ vehicle.vin }} · Placa: {{ vehicle.plate }}</small></td><td><span class="status-pill" :class="vehicle.is_active ? 'active' : 'disabled'"><span class="status-dot"></span>{{ vehicle.is_active ? 'Activo' : 'Deshabilitado' }}</span></td><td class="action-cell"><button type="button" class="table-action" @click="openPreview(vehicle)">Visualizar</button><button type="button" class="table-action" @click="openEdit(vehicle)">Editar</button><button type="button" class="table-action" :class="vehicle.is_active ? 'danger' : 'confirm'" :disabled="busyId === vehicle.id" @click="toggleStatus(vehicle)">{{ vehicle.is_active ? 'Deshabilitar' : 'Reactivar' }}</button></td></tr></tbody></table></div><div v-else class="empty-state table-empty">No hay vehículos que coincidan con la búsqueda.</div><p class="no-delete-note"><span>⌁</span> Deshabilitar conserva el historial del vehículo; no se elimina físicamente.</p></section>

    <div v-if="previewing" class="modal-backdrop" role="presentation" @click.self="closePreview"><section class="modal-card vehicle-preview-modal" role="dialog" aria-modal="true" aria-labelledby="vehicle-preview-title"><div class="modal-heading"><div><p class="eyebrow">DETALLE DEL VEHÍCULO</p><h2 id="vehicle-preview-title">{{ previewing.brand }} {{ previewing.model }}</h2></div><button type="button" class="modal-close" aria-label="Cerrar detalle del vehículo" @click="closePreview">×</button></div><div class="vehicle-preview-photo"><img v-if="previewing.photo_url" :src="previewing.photo_url" :alt="`Foto de ${previewing.brand} ${previewing.model}`" /><div v-else class="vehicle-photo-empty-large">Este vehículo todavía no tiene foto.</div></div><div class="vehicle-preview-data"><div><span>Cliente asociado</span><strong>{{ previewing.customer_name || 'Cliente no disponible' }}</strong></div><div><span>Correo del cliente</span><strong>{{ previewing.customer_email || 'Sin correo' }}</strong></div><div><span>Teléfono del cliente</span><strong>{{ previewing.customer_phone || 'Sin teléfono' }}</strong></div><div><span>Taller</span><strong>{{ selectedWorkshop?.name || 'Taller no disponible' }}</strong></div><div><span>VIN del sistema</span><strong>{{ previewing.system_vin }}</strong></div><div><span>VIN del automóvil</span><strong>{{ previewing.vin }}</strong></div><div><span>Placa</span><strong>{{ previewing.plate }}</strong></div><div><span>Marca y modelo</span><strong>{{ previewing.brand }} {{ previewing.model }}</strong></div><div><span>Año</span><strong>{{ previewing.year }}</strong></div><div><span>Versión</span><strong>{{ previewing.version }}</strong></div><div><span>Color</span><strong>{{ previewing.color }}</strong></div><div><span>Kilometraje</span><strong>{{ previewing.mileage === null ? 'No capturado' : `${previewing.mileage.toLocaleString()} km` }}</strong></div><div><span>Técnico asignado</span><strong>{{ previewing.technician_id || 'Sin asignar' }}</strong></div><div><span>Estado del vehículo</span><strong>{{ previewing.is_active ? 'Activo' : 'Deshabilitado' }}</strong></div><div><span>Estado del cliente</span><strong>{{ previewing.customer_is_active ? 'Activo' : 'Deshabilitado' }}</strong></div></div><div class="modal-actions"><button type="button" class="secondary" @click="closePreview">Cerrar</button></div></section></div>

    <div v-if="editing" class="modal-backdrop" role="presentation" @click.self="closeEdit"><section class="modal-card vehicle-edit-modal" role="dialog" aria-modal="true" aria-labelledby="vehicle-edit-title"><div class="modal-heading"><div><p class="eyebrow">ACTUALIZAR VEHÍCULO</p><h2 id="vehicle-edit-title">{{ editing.brand }} {{ editing.model }}</h2></div><button type="button" class="modal-close" aria-label="Cerrar modal" @click="closeEdit">×</button></div><div class="readonly-workshop"><p class="eyebrow">CLIENTE Y TALLER — SOLO LECTURA</p><strong>{{ editing.customer_name || 'Cliente no disponible' }}</strong><small>{{ editing.customer_email || 'Sin correo' }} · {{ selectedWorkshop?.name || 'Taller no disponible' }}</small><small>VIN del sistema: {{ editing.system_vin }} · Técnico: {{ editing.technician_id || 'Sin asignar' }}</small></div><form @submit.prevent="saveEdit"><div class="field-grid"><label>VIN del automóvil<input :value="editing.vin" readonly aria-readonly="true" autocomplete="off" /><small>Identificador permanente; no se puede editar.</small></label><label>Placa<input v-model="editForm.plate" required minlength="4" maxlength="10" autocomplete="off" /></label><label>Marca<input v-model="editForm.brand" required minlength="2" maxlength="80" /></label><label>Modelo<input v-model="editForm.model" required minlength="1" maxlength="80" /></label><label>Año<input v-model.number="editForm.year" required type="number" min="1886" :max="yearMax" /></label><label>Versión<input v-model="editForm.version" required minlength="1" maxlength="80" /></label><label>Color<input v-model="editForm.color" required minlength="2" maxlength="50" /></label><label>Kilometraje<input v-model.number="editForm.mileage" required type="number" min="0" max="2000000" /></label></div><p v-if="formError" class="form-error" role="alert">{{ formError }}</p><p class="modal-note">Todos los datos editables son obligatorios. El VIN permanece protegido y no se modifica; el sistema valida la placa para evitar duplicados.</p><div class="modal-actions"><button type="button" class="secondary" :disabled="busy" @click="closeEdit">Cancelar</button><button class="primary" :disabled="busy">{{ busy ? 'Guardando…' : 'Guardar cambios' }}</button></div></form></section></div>
    <ConfirmationDialog :request="confirmation" :busy="confirmationBusy" @confirm="confirmPendingAction" @cancel="cancelPendingAction" />
  </main>
</template>
