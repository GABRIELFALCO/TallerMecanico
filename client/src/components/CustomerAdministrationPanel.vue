<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import ConfirmationDialog from '@/components/ConfirmationDialog.vue'
import type { ConfirmationRequest, Customer, Workshop } from '@/types'

const emit = defineEmits<{
  notice: [kind: 'success' | 'error', text: string]
  'open-vehicle': [customer: Customer]
}>()

const workshops = ref<Workshop[]>([])
const customers = ref<Customer[]>([])
const selectedWorkshopId = ref('')
const search = ref('')
const editing = ref<Customer | null>(null)
const loading = ref(false)
const busy = ref(false)
const busyId = ref<string | null>(null)
const confirmationBusy = ref(false)
const confirmation = ref<ConfirmationRequest | null>(null)
const pendingCustomer = ref<Customer | null>(null)
const editForm = reactive({ fullName: '', phone: '', email: '' })

const selectedWorkshop = computed(() => workshops.value.find((workshop) => workshop.id === selectedWorkshopId.value))
const activeCustomers = computed(() => customers.value.filter((customer) => customer.is_active).length)
const disabledCustomers = computed(() => customers.value.filter((customer) => !customer.is_active).length)
const filteredCustomers = computed(() => {
  const needle = search.value.trim().toLowerCase()
  if (!needle) return customers.value
  return customers.value.filter((customer) => [customer.full_name, customer.phone, customer.email].some((value) => value.toLowerCase().includes(needle)))
})

async function loadWorkshops() {
  try {
    workshops.value = await tallerMecanicoFacade.listWorkshops()
    selectedWorkshopId.value = workshops.value.find((item) => item.is_active && ['admin', 'reception'].includes(item.role))?.id ?? ''
    await loadCustomers()
  } catch (error) {
    emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los talleres.')
  }
}

async function loadCustomers() {
  if (!selectedWorkshopId.value || !selectedWorkshop.value?.is_active) {
    customers.value = []
    return
  }
  loading.value = true
  try {
    customers.value = await tallerMecanicoFacade.listCustomers(selectedWorkshopId.value)
  } catch (error) {
    emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los clientes.')
  } finally { loading.value = false }
}

function openEdit(customer: Customer) {
  editing.value = customer
  editForm.fullName = customer.full_name
  editForm.phone = customer.phone
  editForm.email = customer.email
}

function closeEdit() {
  if (!busy.value) editing.value = null
}

async function saveEdit() {
  if (!editing.value || !selectedWorkshopId.value) return
  busy.value = true
  try {
    const updated = await tallerMecanicoFacade.updateCustomer(selectedWorkshopId.value, editing.value.id, editForm.fullName, editForm.phone, editForm.email)
    const index = customers.value.findIndex((customer) => customer.id === updated.id)
    if (index >= 0) customers.value[index] = { ...customers.value[index], ...updated }
    editing.value = null
    emit('notice', 'success', updated.message ?? 'Cliente actualizado correctamente.')
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo actualizar el cliente.') } finally { busy.value = false }
}

function toggleStatus(customer: Customer) {
  if (!selectedWorkshopId.value) return
  const action = customer.is_active ? 'deshabilitar' : 'reactivar'
  pendingCustomer.value = customer
  confirmation.value = {
    title: customer.is_active ? 'Deshabilitar cliente' : 'Reactivar cliente',
    message: customer.is_active
      ? `Se deshabilitará a ${customer.full_name}. Sus datos e historial se conservarán.`
      : `Se volverá a habilitar a ${customer.full_name} para las operaciones del taller.`,
    confirmLabel: `${action[0].toUpperCase()}${action.slice(1)} cliente`,
    variant: customer.is_active ? 'danger' : 'standard',
  }
}

function cancelStatusChange() {
  if (confirmationBusy.value) return
  confirmation.value = null
  pendingCustomer.value = null
}

async function confirmStatusChange() {
  const customer = pendingCustomer.value
  if (!customer || !selectedWorkshopId.value || confirmationBusy.value) return
  confirmationBusy.value = true
  busyId.value = customer.id
  try {
    const result = await tallerMecanicoFacade.updateCustomerStatus(selectedWorkshopId.value, customer.id, !customer.is_active)
    customer.is_active = result.is_active
    emit('notice', 'success', result.message)
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo actualizar el estado del cliente.') }
  finally {
    busyId.value = null
    confirmationBusy.value = false
    confirmation.value = null
    pendingCustomer.value = null
  }
}

watch(selectedWorkshopId, loadCustomers)
onMounted(loadWorkshops)
</script>

<template>
  <main class="dashboard roles-page customer-page">
    <section class="dashboard-title roles-heading"><p class="eyebrow">RECEPCIÓN Y CLIENTES</p><h1>Administración de clientes.</h1><p>Consulta, actualiza y conserva el historial de clientes por taller.</p></section>
    <section class="role-summary"><article class="role-stat"><span class="stat-icon">♙</span><div><strong>{{ customers.length }}</strong><span>clientes registrados</span></div></article><article class="role-stat"><span class="stat-icon green">✓</span><div><strong>{{ activeCustomers }}</strong><span>clientes activos</span></div></article><article class="role-stat"><span class="stat-icon gold">!</span><div><strong>{{ disabledCustomers }}</strong><span>deshabilitados</span></div></article></section>
    <section class="customer-toolbar form-card"><label>Taller de trabajo<select v-model="selectedWorkshopId"><option value="" disabled>Selecciona un taller activo</option><option v-for="workshop in workshops.filter((item) => ['admin', 'reception'].includes(item.role))" :key="workshop.id" :value="workshop.id">{{ workshop.name }} · {{ workshop.is_active ? 'Activo' : 'Inactivo' }}</option></select></label><label>Buscar cliente<input v-model.trim="search" type="search" placeholder="Nombre, teléfono o correo" /></label><span v-if="selectedWorkshop" class="selected-workshop">{{ selectedWorkshop.name }} · {{ selectedWorkshop.is_active ? 'Activo' : 'Inactivo' }}</span></section>
    <section class="form-card role-table-card"><div class="table-heading"><div><p class="eyebrow">REGISTROS DEL TALLER</p><h2>Clientes</h2></div><span class="table-count">{{ filteredCustomers.length }} resultados</span></div><div v-if="loading" class="empty-state table-empty">Cargando clientes…</div><div v-else-if="!selectedWorkshop" class="empty-state table-empty">Selecciona un taller activo para consultar sus clientes.</div><div v-else-if="filteredCustomers.length" class="role-table-wrap"><table class="role-table customer-table" aria-label="Clientes registrados en el taller"><colgroup><col class="customer-column" /><col class="contact-column" /><col class="status-column" /><col class="actions-column" /></colgroup><thead><tr><th>Cliente</th><th>Contacto</th><th>Estado</th><th>Acciones</th></tr></thead><tbody><tr v-for="customer in filteredCustomers" :key="customer.id" :class="{ inactive: !customer.is_active }"><td><div class="customer-table-stack"><strong>{{ customer.full_name }}</strong><small>{{ customer.workshop.name }}</small></div></td><td><div class="customer-table-stack"><span>{{ customer.phone }}</span><small>{{ customer.email }}</small></div></td><td><span class="status-pill" :class="customer.is_active ? 'active' : 'disabled'"><span class="status-dot"></span>{{ customer.is_active ? 'Activo' : 'Deshabilitado' }}</span></td><td class="action-cell"><div class="customer-actions"><button class="table-action" @click="openEdit(customer)">Editar</button><button v-if="customer.is_active" class="table-action" @click="emit('open-vehicle', customer)">Asociar vehículo</button><button class="table-action" :class="customer.is_active ? 'danger' : 'confirm'" :disabled="busyId === customer.id" @click="toggleStatus(customer)">{{ customer.is_active ? 'Deshabilitar' : 'Reactivar' }}</button></div></td></tr></tbody></table></div><div v-else class="empty-state table-empty">No hay clientes que coincidan con la búsqueda.</div><p class="no-delete-note"><span>⌁</span> Deshabilitar conserva los datos y el historial; no se elimina físicamente el cliente.</p></section>

    <div v-if="editing" class="modal-backdrop" role="presentation" @click.self="closeEdit"><section class="modal-card" role="dialog" aria-modal="true" aria-labelledby="customer-edit-title"><div class="modal-heading"><div><p class="eyebrow">ACTUALIZAR CLIENTE</p><h2 id="customer-edit-title">{{ editing.full_name }}</h2></div><button type="button" class="modal-close" aria-label="Cerrar modal" @click="closeEdit">×</button></div><div class="readonly-workshop"><p class="eyebrow">TALLER — SOLO LECTURA</p><strong>{{ editing.workshop.name }}</strong><small>RFC: {{ editing.workshop.tax_id || 'Pendiente' }} · {{ editing.workshop.state || 'Ubicación pendiente' }}, {{ editing.workshop.municipality || '' }}</small><small>{{ editing.workshop.locality || '' }} · {{ editing.workshop.colony || '' }} · CP {{ editing.workshop.postal_code || '—' }}</small></div><form @submit.prevent="saveEdit"><label>Nombre completo<input v-model.trim="editForm.fullName" required minlength="5" pattern="[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+" /></label><div class="field-grid"><label>Teléfono<input v-model.trim="editForm.phone" required minlength="10" maxlength="25" inputmode="tel" /></label><label>Correo electrónico<input v-model.trim="editForm.email" type="email" required /></label></div><p class="modal-note">Se conservarán dos medios de contacto y se verificará que no existan duplicados en este taller.</p><div class="modal-actions"><button type="button" class="secondary" :disabled="busy" @click="closeEdit">Cancelar</button><button class="primary" :disabled="busy">{{ busy ? 'Guardando…' : 'Guardar cambios' }}</button></div></form></section></div>
    <ConfirmationDialog :request="confirmation" :busy="confirmationBusy" @confirm="confirmStatusChange" @cancel="cancelStatusChange" />
  </main>
</template>
