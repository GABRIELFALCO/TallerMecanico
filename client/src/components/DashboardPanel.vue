<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '@/api'
import type { User, Workshop } from '@/types'

const props = defineProps<{ user: User }>()
const emit = defineEmits<{ logout: []; notice: [kind: 'success' | 'error', text: string] }>()
const workshops = ref<Workshop[]>([])
const selectedId = ref('')
const busy = ref(false)
const workshopForm = reactive({ name: '', taxId: '' })
const customerForm = reactive({ name: '', phone: '', email: '' })
const activeWorkshop = computed(() => workshops.value.find((workshop) => workshop.id === selectedId.value))
const canRegisterCustomers = computed(() => ['owner', 'manager', 'reception'].includes(activeWorkshop.value?.role ?? ''))

function focusNewWorkshop() {
  document.querySelector<HTMLInputElement>('#new-workshop-name')?.focus()
}

async function loadWorkshops() {
  try {
    workshops.value = await api.workshops()
    selectedId.value = workshops.value.find((item) => item.is_active)?.id ?? workshops.value[0]?.id ?? ''
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los talleres.') }
}

async function addWorkshop() {
  busy.value = true
  try {
    const workshop = await api.createWorkshop(workshopForm.name, workshopForm.taxId)
    workshopForm.name = ''; workshopForm.taxId = ''
    await loadWorkshops(); selectedId.value = workshop.id
    emit('notice', 'success', 'Taller creado y seleccionado correctamente.')
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo crear el taller.') } finally { busy.value = false }
}

async function addCustomer() {
  if (!selectedId.value) return
  busy.value = true
  try {
    const result = await api.createCustomer(selectedId.value, customerForm.name, customerForm.phone, customerForm.email)
    customerForm.name = ''; customerForm.phone = ''; customerForm.email = ''
    emit('notice', 'success', result.message)
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo registrar el cliente.') } finally { busy.value = false }
}

async function signOut() {
  try { await api.logout(); emit('logout'); emit('notice', 'success', 'Sesión cerrada correctamente.') }
  catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo cerrar la sesión.') }
}

onMounted(loadWorkshops)
</script>

<template>
  <main class="dashboard">
    <header class="dashboard-header"><a class="small-brand"><b>TM</b> Taller Mecánico</a><div class="profile"><span>{{ props.user.full_name }}</span><button @click="signOut">Cerrar sesión</button></div></header>
    <section class="dashboard-title"><p class="eyebrow">PANEL DE CONTROL</p><h1>Buenos días, {{ props.user.full_name.split(' ')[0] }}.</h1><p>Selecciona un taller para trabajar de manera aislada y segura.</p></section>
    <section class="workshop-strip" aria-label="Talleres disponibles">
      <button v-for="workshop in workshops" :key="workshop.id" class="workshop-chip" :class="{ selected: selectedId === workshop.id }" @click="selectedId = workshop.id"><span class="dot" :class="{ off: !workshop.is_active }"></span><b>{{ workshop.name }}</b><small>{{ workshop.role }}</small></button>
      <button class="add-chip" @click="focusNewWorkshop">+ Nuevo taller</button>
    </section>
    <section v-if="activeWorkshop" class="workspace-grid">
      <article class="overview-card"><p class="eyebrow">TALLER ACTIVO</p><h2>{{ activeWorkshop.name }}</h2><div class="status-line"><span class="dot" :class="{ off: !activeWorkshop.is_active }"></span>{{ activeWorkshop.is_active ? 'Taller activo y autorizado' : 'Taller inactivo' }}</div><p>Tu rol actual: <strong>{{ activeWorkshop.role }}</strong></p><div class="role-note">{{ canRegisterCustomers ? 'Puedes registrar clientes desde recepción.' : 'Tu rol es de consulta; solicita acceso a un administrador para registrar clientes.' }}</div></article>
      <article class="form-card"><h2>Registrar cliente</h2><p>Datos mínimos para abrir su historial.</p><form v-if="canRegisterCustomers && activeWorkshop.is_active" @submit.prevent="addCustomer"><label>Nombre completo<input v-model.trim="customerForm.name" required minlength="3" placeholder="Nombre del cliente" /></label><div class="field-grid"><label>Teléfono<input v-model.trim="customerForm.phone" required minlength="7" placeholder="55 0000 0000" /></label><label>Correo <small>(opcional)</small><input v-model.trim="customerForm.email" type="email" placeholder="cliente@email.com" /></label></div><button class="primary" :disabled="busy">{{ busy ? 'Guardando…' : 'Registrar cliente' }}</button></form><p v-else class="empty-state">No tienes autorización para registrar clientes en este taller.</p></article>
      <article class="form-card new-workshop"><h2>Agregar otro taller</h2><p>Podrás cambiar entre negocios con la misma cuenta.</p><form @submit.prevent="addWorkshop"><label>Nombre del taller<input id="new-workshop-name" v-model.trim="workshopForm.name" required minlength="3" placeholder="Ej. Taller Centro" /></label><label>RFC <small>(opcional)</small><input v-model.trim="workshopForm.taxId" maxlength="32" placeholder="XAXX010101000" /></label><button class="secondary" :disabled="busy">{{ busy ? 'Creando…' : 'Crear taller' }}</button></form></article>
    </section>
  </main>
</template>
