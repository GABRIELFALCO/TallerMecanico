<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import type { Role, User, Workshop } from '@/types'

const props = defineProps<{ user: User }>()
const emit = defineEmits<{ notice: [kind: 'success' | 'error', text: string] }>()
const workshops = ref<Workshop[]>([])
const selectedId = ref('')
const busy = ref(false)
const customerForm = reactive({ name: '', phone: '', email: '' })
const activeWorkshop = computed(() => workshops.value.find((workshop) => workshop.id === selectedId.value))
const canRegisterCustomers = computed(() => ['admin', 'reception'].includes(activeWorkshop.value?.role ?? ''))
const roleNames: Record<Role, string> = {
  admin: 'Administrador',
  reception: 'Recepcionista',
  service_advisor: 'Asesor de servicio',
  technician: 'Técnico',
  customer: 'Cliente',
  system: 'Sistema',
}

function roleLabel(role: Role): string {
  return roleNames[role]
}

async function loadWorkshops() {
  try {
    workshops.value = await tallerMecanicoFacade.listWorkshops()
    selectedId.value = workshops.value.find((item) => item.is_active)?.id ?? workshops.value[0]?.id ?? ''
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los talleres.') }
}

async function addCustomer() {
  if (!selectedId.value) return
  busy.value = true
  try {
    const result = await tallerMecanicoFacade.registerCustomer(selectedId.value, { fullName: customerForm.name, phone: customerForm.phone, email: customerForm.email })
    customerForm.name = ''; customerForm.phone = ''; customerForm.email = ''
    emit('notice', 'success', result.message)
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo registrar el cliente.') } finally { busy.value = false }
}

onMounted(loadWorkshops)
</script>

<template>
  <main class="dashboard">
    <section class="dashboard-title"><p class="eyebrow">PANEL DE CONTROL</p><h1>Buenos días, {{ props.user.full_name.split(' ')[0] }}.</h1><p>Selecciona un taller para trabajar de manera aislada y segura.</p></section>
    <section class="workshop-strip" aria-label="Talleres disponibles">
      <button v-for="workshop in workshops" :key="workshop.id" class="workshop-chip" :class="{ selected: selectedId === workshop.id }" @click="selectedId = workshop.id"><span class="dot" :class="{ off: !workshop.is_active }"></span><b>{{ workshop.name }}</b><small>{{ roleLabel(workshop.role) }}</small></button>
    </section>
    <section v-if="activeWorkshop" class="workspace-grid">
      <article class="overview-card"><p class="eyebrow">TALLER ACTIVO</p><h2>{{ activeWorkshop.name }}</h2><div class="status-line"><span class="dot" :class="{ off: !activeWorkshop.is_active }"></span>{{ activeWorkshop.is_active ? 'Taller activo y autorizado' : 'Taller inactivo' }}</div><p>Tu rol actual: <strong>{{ roleLabel(activeWorkshop.role) }}</strong></p><div class="role-note">{{ canRegisterCustomers ? 'Puedes registrar clientes desde recepción.' : 'Tu rol es de consulta; solicita acceso a un administrador para registrar clientes.' }}</div></article>
      <article class="form-card"><h2>Registrar cliente</h2><p>Se requieren nombre completo y dos medios de contacto.</p><form v-if="canRegisterCustomers && activeWorkshop.is_active" @submit.prevent="addCustomer"><label>Nombre completo<input v-model.trim="customerForm.name" required minlength="5" pattern="[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+" placeholder="Nombre y apellidos" /><small>Escribe al menos nombre y apellido.</small></label><div class="field-grid"><label>Teléfono<input v-model.trim="customerForm.phone" required minlength="10" maxlength="25" inputmode="tel" placeholder="55 0000 0000" /><small>10 a 15 dígitos.</small></label><label>Correo electrónico<input v-model.trim="customerForm.email" type="email" required placeholder="cliente@email.com" /><small>Segundo medio de contacto.</small></label></div><label class="confirm-check"><input type="checkbox" required /> Confirmo que deseo crear este registro de cliente.</label><button class="primary" :disabled="busy">{{ busy ? 'Guardando…' : 'Registrar cliente' }}</button></form><p v-else class="empty-state">No tienes autorización para registrar clientes en este taller.</p></article>
    </section>
  </main>
</template>
