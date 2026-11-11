<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import ConfirmationDialog from '@/components/ConfirmationDialog.vue'
import type { ConfirmationRequest, Role, User, Workshop } from '@/types'

defineProps<{ user: User }>()
const emit = defineEmits<{ notice: [kind: 'success' | 'error', text: string] }>()

const workshops = ref<Workshop[]>([])
const selectedId = ref('')
const busy = ref(false)
const confirmationBusy = ref(false)
const confirmation = ref<ConfirmationRequest | null>(null)
const roleForm = reactive({ email: '', role: 'reception' as Role })
const activeWorkshops = computed(() => workshops.value.filter((workshop) => workshop.role === 'admin' && workshop.is_active))
const selectedWorkshop = computed(() => activeWorkshops.value.find((workshop) => workshop.id === selectedId.value))

const roleOptions: Array<{ code: Role; name: string; description: string }> = [
  { code: 'admin', name: 'Administrador', description: 'Gestiona usuarios, roles y operación.' },
  { code: 'reception', name: 'Recepcionista', description: 'Registra clientes y atiende recepción.' },
  { code: 'service_advisor', name: 'Asesor de servicio', description: 'Da seguimiento a servicios y clientes.' },
  { code: 'technician', name: 'Técnico', description: 'Trabaja con la información técnica asignada.' },
  { code: 'customer', name: 'Cliente', description: 'Consulta su información autorizada.' },
  { code: 'system', name: 'Sistema', description: 'Cuenta reservada para procesos internos.' },
]

function roleName(code: Role): string {
  return roleOptions.find((option) => option.code === code)?.name ?? code
}

async function loadWorkshops() {
  try {
    workshops.value = await tallerMecanicoFacade.listWorkshops()
    selectedId.value = activeWorkshops.value[0]?.id ?? ''
    if (!selectedId.value) emit('notice', 'error', 'No tienes un taller activo con rol de administrador.')
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los talleres administrables.') }
}

async function assignRole() {
  if (!selectedId.value) {
    emit('notice', 'error', 'Selecciona un taller activo.')
    return
  }
  confirmation.value = {
    title: 'Confirmar asignación de rol',
    message: `Se asignará el rol ${roleName(roleForm.role)} a ${roleForm.email.trim()} en ${selectedWorkshop.value?.name ?? 'el taller seleccionado'}.`,
    confirmLabel: 'Asignar rol',
    variant: 'standard',
  }
}

async function confirmAssignment() {
  if (!selectedId.value || confirmationBusy.value) return
  confirmationBusy.value = true
  busy.value = true
  try {
    const result = await tallerMecanicoFacade.assignRole(selectedId.value, roleForm.email, roleForm.role)
    roleForm.email = ''
    emit('notice', 'success', result.message)
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo asignar el rol.') } finally {
    busy.value = false
    confirmationBusy.value = false
    confirmation.value = null
  }
}

function cancelAssignment() {
  if (!confirmationBusy.value) confirmation.value = null
}

onMounted(loadWorkshops)
</script>

<template>
  <main class="dashboard roles-page">
    <section class="dashboard-title roles-heading"><p class="eyebrow">ADMINISTRACIÓN DE ACCESOS</p><h1>Crear y asignar roles.</h1><p>Autoriza a las personas correctas dentro de cada taller, sin mezclar negocios.</p></section>
    <section class="role-summary">
      <article class="role-stat"><span class="stat-icon">♙</span><div><strong>{{ roleOptions.length }}</strong><span>roles del sistema</span></div></article>
      <article class="role-stat"><span class="stat-icon green">✓</span><div><strong>{{ activeWorkshops.length }}</strong><span>talleres administrables</span></div></article>
      <article class="role-stat"><span class="stat-icon gold">⌁</span><div><strong>Admin</strong><span>único rol autorizado</span></div></article>
    </section>
    <section class="role-workspace">
      <article class="form-card role-assignment-card">
        <p class="eyebrow">NUEVA ASIGNACIÓN</p><h2>Autorizar una cuenta</h2><p>La cuenta debe existir antes de recibir un rol dentro del taller.</p>
        <form @submit.prevent="assignRole">
          <label>Taller activo<select v-model="selectedId" required :disabled="!activeWorkshops.length"><option value="" disabled>Selecciona un taller</option><option v-for="workshop in activeWorkshops" :key="workshop.id" :value="workshop.id">{{ workshop.name }}</option></select></label>
          <div v-if="selectedWorkshop" class="selected-workshop"><span class="dot"></span><span>{{ selectedWorkshop.name }}</span><small>Administrador autorizado</small></div>
          <label>Correo de la cuenta<input v-model.trim="roleForm.email" required type="email" placeholder="persona@correo.com" /><small>Debe ser una cuenta registrada previamente.</small></label>
          <label>Rol a asignar<select v-model="roleForm.role"><option v-for="role in roleOptions" :key="role.code" :value="role.code">{{ role.name }}</option></select></label>
          <div class="role-description"><strong>{{ roleName(roleForm.role) }}</strong><span>{{ roleOptions.find((role) => role.code === roleForm.role)?.description }}</span></div>
          <button class="primary" :disabled="busy || !activeWorkshops.length">{{ busy ? 'Asignando…' : 'Asignar rol' }}</button>
        </form>
      </article>
      <article class="roles-catalog">
        <p class="eyebrow">CATÁLOGO ACTIVO</p><h2>Roles disponibles</h2><p>Estos son los perfiles que puedes asignar en el taller seleccionado.</p>
        <ul><li v-for="role in roleOptions" :key="role.code" :class="{ selected: roleForm.role === role.code }" @click="roleForm.role = role.code"><span class="role-badge">{{ role.name.charAt(0) }}</span><span><strong>{{ role.name }}</strong><small>{{ role.description }}</small></span><span class="arrow">›</span></li></ul>
      </article>
    </section>
    <ConfirmationDialog :request="confirmation" :busy="confirmationBusy" @confirm="confirmAssignment" @cancel="cancelAssignment" />
  </main>
</template>
