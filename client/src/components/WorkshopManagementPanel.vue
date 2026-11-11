<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import ConfirmationDialog from '@/components/ConfirmationDialog.vue'
import WorkshopAddressFields from '@/components/WorkshopAddressFields.vue'
import type { ConfirmationRequest, Workshop, WorkshopAddress } from '@/types'

type PendingConfirmation = { kind: 'create' } | { kind: 'update' } | { kind: 'status'; workshop: Workshop }

const emit = defineEmits<{ notice: [kind: 'success' | 'error', text: string] }>()
const workshops = ref<Workshop[]>([])
const selectedId = ref('')
const busy = ref(false)
const busyId = ref<string | null>(null)
const previewing = ref<Workshop | null>(null)
const photoFile = ref<File | null>(null)
const photoPreview = ref<string | null>(null)
const photoInput = ref<HTMLInputElement | null>(null)
const photoError = ref('')
const confirmation = ref<ConfirmationRequest | null>(null)
const pendingConfirmation = ref<PendingConfirmation | null>(null)
const confirmationBusy = ref(false)
const maxPhotoBytes = 5 * 1024 * 1024
const emptyAddress = (): WorkshopAddress => ({ state: '', municipality: '', locality: '', colony: '', postal_code: '' })
const createForm = reactive({ name: '', taxId: '', address: emptyAddress() })
const editForm = reactive({ name: '', taxId: '', address: emptyAddress() })
const selectedWorkshop = computed(() => workshops.value.find((workshop) => workshop.id === selectedId.value))
const activeCount = computed(() => workshops.value.filter((workshop) => workshop.is_active).length)
const inactiveCount = computed(() => workshops.value.filter((workshop) => !workshop.is_active).length)
const createStep = computed(() => {
  if (!createForm.name.trim() || !createForm.taxId.trim()) return 1
  const addressComplete = Object.values(createForm.address).every((value) => value.trim().length > 0)
  return addressComplete ? 3 : 2
})

function addressFromWorkshop(workshop: Workshop): WorkshopAddress {
  return {
    state: workshop.state ?? '',
    municipality: workshop.municipality ?? '',
    locality: workshop.locality ?? '',
    colony: workshop.colony ?? '',
    postal_code: workshop.postal_code ?? '',
  }
}

function selectPhoto(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  photoError.value = ''
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    photoError.value = 'Elige una imagen JPG, PNG o WebP.'
    input.value = ''
    return
  }
  if (file.size > maxPhotoBytes) {
    photoError.value = 'La foto no debe superar los 5 MB.'
    input.value = ''
    return
  }
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photoFile.value = file
  photoPreview.value = URL.createObjectURL(file)
}

function clearPhoto() {
  photoFile.value = null
  photoError.value = ''
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photoPreview.value = null
  if (photoInput.value) photoInput.value.value = ''
}

function readPhotoAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => typeof reader.result === 'string' ? resolve(reader.result) : reject(new Error('No se pudo leer la foto.'))
    reader.onerror = () => reject(new Error('No se pudo leer la foto seleccionada.'))
    reader.readAsDataURL(file)
  })
}

function chooseWorkshop(workshop: Workshop) {
  selectedId.value = workshop.id
  editForm.name = workshop.name
  editForm.taxId = workshop.tax_id ?? ''
  editForm.address = addressFromWorkshop(workshop)
}

async function loadWorkshops() {
  try {
    workshops.value = await tallerMecanicoFacade.listAdminWorkshops()
    if (workshops.value.length) chooseWorkshop(workshops.value[0])
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los talleres administrables.') }
}

function createWorkshop() {
  if (photoError.value) return
  pendingConfirmation.value = { kind: 'create' }
  confirmation.value = {
    title: 'Crear taller',
    message: `Se registrará ${createForm.name.trim()} con el RFC ${createForm.taxId.trim().toUpperCase()} y la ubicación indicada.`,
    confirmLabel: 'Crear taller',
    variant: 'standard',
  }
}

async function persistCreateWorkshop() {
  busy.value = true
  try {
    const photoDataUrl = photoFile.value ? await readPhotoAsDataUrl(photoFile.value) : undefined
    const workshop = await tallerMecanicoFacade.createWorkshop(createForm.name, createForm.taxId, createForm.address, photoDataUrl)
    createForm.name = ''; createForm.taxId = ''; createForm.address = emptyAddress()
    clearPhoto()
    await loadWorkshops(); chooseWorkshop(workshop)
    emit('notice', 'success', 'Taller creado y asociado correctamente.')
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo crear el taller.') } finally { busy.value = false }
}

function updateWorkshop() {
  if (!selectedWorkshop.value) return
  pendingConfirmation.value = { kind: 'update' }
  confirmation.value = {
    title: 'Guardar cambios del taller',
    message: `Se actualizarán los datos fiscales y la ubicación de ${selectedWorkshop.value.name}.`,
    confirmLabel: 'Guardar cambios',
    variant: 'standard',
  }
}

async function persistUpdateWorkshop() {
  if (!selectedId.value) return
  busyId.value = selectedId.value
  try {
    const workshop = await tallerMecanicoFacade.updateWorkshop(selectedId.value, editForm.name, editForm.taxId, editForm.address)
    const index = workshops.value.findIndex((item) => item.id === workshop.id)
    if (index >= 0) workshops.value[index] = workshop
    emit('notice', 'success', 'Taller actualizado correctamente.')
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo actualizar el taller.') } finally { busyId.value = null }
}

function toggleStatus(workshop: Workshop) {
  pendingConfirmation.value = { kind: 'status', workshop }
  confirmation.value = {
    title: workshop.is_active ? 'Deshabilitar taller' : 'Reactivar taller',
    message: workshop.is_active
      ? `Se deshabilitará ${workshop.name}. El historial se conservará y el taller dejará de estar disponible para sus operaciones.`
      : `${workshop.name} volverá a estar disponible para las operaciones autorizadas.`,
    confirmLabel: workshop.is_active ? 'Deshabilitar taller' : 'Reactivar taller',
    variant: workshop.is_active ? 'danger' : 'standard',
  }
}

async function persistWorkshopStatus(workshop: Workshop) {
  busyId.value = workshop.id
  try {
    const result = await tallerMecanicoFacade.updateWorkshopStatus(workshop.id, !workshop.is_active)
    workshop.is_active = !workshop.is_active
    emit('notice', 'success', result.message)
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo actualizar el estado del taller.') } finally { busyId.value = null }
}

async function confirmPendingAction() {
  const action = pendingConfirmation.value
  if (!action || confirmationBusy.value) return
  confirmationBusy.value = true
  try {
    if (action.kind === 'create') await persistCreateWorkshop()
    else if (action.kind === 'update') await persistUpdateWorkshop()
    else await persistWorkshopStatus(action.workshop)
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

watch(selectedId, (id) => {
  const workshop = workshops.value.find((item) => item.id === id)
  if (workshop) chooseWorkshop(workshop)
})
onMounted(loadWorkshops)
onBeforeUnmount(() => { if (photoPreview.value) URL.revokeObjectURL(photoPreview.value) })
</script>

<template>
  <main class="dashboard roles-page workshop-management-page">
    <section class="dashboard-title roles-heading"><p class="eyebrow">ADMINISTRACIÓN DE NEGOCIOS</p><h1>Alta del taller mecánico.</h1><p>Registra y administra tus empresas con una identidad fiscal validada.</p></section>
    <section class="role-summary"><article class="role-stat"><span class="stat-icon">▣</span><div><strong>{{ workshops.length }}</strong><span>talleres registrados</span></div></article><article class="role-stat"><span class="stat-icon green">✓</span><div><strong>{{ activeCount }}</strong><span>talleres activos</span></div></article><article class="role-stat"><span class="stat-icon gold">!</span><div><strong>{{ inactiveCount }}</strong><span>deshabilitados</span></div></article></section>
    <section class="workshop-management-grid">
      <article class="form-card"><p class="eyebrow">NUEVA EMPRESA</p><h2>Dar de alta un taller</h2><p>Completa la identidad fiscal y la ubicación del negocio.</p><div class="creation-progress" aria-label="Progreso de creación del taller"><div :class="{ current: createStep === 1, complete: createStep > 1 }"><span>1</span><small>Identidad fiscal</small></div><i></i><div :class="{ current: createStep === 2, complete: createStep > 2 }"><span>2</span><small>Ubicación</small></div><i></i><div :class="{ current: createStep === 3 }"><span>3</span><small>Confirmar</small></div></div><form @submit.prevent="createWorkshop"><label>Nombre comercial<input v-model.trim="createForm.name" required minlength="3" maxlength="120" placeholder="Taller Centro" /><small>No puede repetirse en el sistema.</small></label><label>RFC<input v-model.trim="createForm.taxId" required minlength="12" maxlength="13" pattern="[A-Za-zÑñ&]{3,4}[0-9]{6}[A-Za-z0-9]{3}" placeholder="ABC010203AB1" style="text-transform: uppercase" /><small>12 o 13 caracteres. Ejemplo: ABC010203AB1.</small></label><WorkshopAddressFields v-model="createForm.address" @notice="(kind, text) => emit('notice', kind, text)" /><label class="photo-upload-field">Foto del taller <small>(opcional)</small><input ref="photoInput" type="file" accept="image/jpeg,image/png,image/webp" @change="selectPhoto" /><small>Formatos JPG, PNG o WebP; máximo 5 MB.</small></label><p v-if="photoError" class="form-error" role="alert">{{ photoError }}</p><div v-if="photoPreview" class="photo-selection"><img :src="photoPreview" alt="Vista previa de la foto del taller" /><div><strong>{{ photoFile?.name }}</strong><small>{{ ((photoFile?.size ?? 0) / 1024 / 1024).toFixed(2) }} MB</small><button type="button" class="table-action danger" @click="clearPhoto">Quitar foto</button></div></div><button class="primary" :disabled="busy || Boolean(photoError)">{{ busy ? 'Creando…' : 'Crear taller' }}</button></form></article>
      <article class="form-card"><p class="eyebrow">TALLER SELECCIONADO</p><h2>{{ selectedWorkshop?.name ?? 'Selecciona un taller' }}</h2><p>Edita los datos fiscales, la ubicación o el estado operativo.</p><div v-if="selectedWorkshop" class="selected-workshop-profile"><div class="workshop-photo-frame"><img v-if="selectedWorkshop.photo_url" :src="selectedWorkshop.photo_url" :alt="`Foto de ${selectedWorkshop.name}`" /><div v-else class="workshop-photo-empty">Sin foto cargada</div></div><div class="selected-workshop-details"><span class="status-pill" :class="selectedWorkshop.is_active ? 'active' : 'disabled'"><span class="status-dot"></span>{{ selectedWorkshop.is_active ? 'Activo' : 'Deshabilitado' }}</span><strong>{{ selectedWorkshop.name }}</strong><span class="rfc-value">RFC {{ selectedWorkshop.tax_id || 'Pendiente' }}</span><small>{{ selectedWorkshop.state || 'Estado pendiente' }} · {{ selectedWorkshop.municipality || 'Municipio pendiente' }}</small><small>{{ selectedWorkshop.locality || 'Sin localidad' }} · {{ selectedWorkshop.colony || 'Colonia pendiente' }} · CP {{ selectedWorkshop.postal_code || '—' }}</small></div></div><form v-if="selectedWorkshop" @submit.prevent="updateWorkshop"><label>Nombre comercial<input v-model.trim="editForm.name" required minlength="3" maxlength="120" /></label><label>RFC<input v-model.trim="editForm.taxId" required minlength="12" maxlength="13" pattern="[A-Za-zÑñ&]{3,4}[0-9]{6}[A-Za-z0-9]{3}" style="text-transform: uppercase" /></label><WorkshopAddressFields v-model="editForm.address" :locality-optional="true" @notice="(kind, text) => emit('notice', kind, text)" /><div class="workshop-edit-actions"><button class="secondary" :disabled="busyId === selectedWorkshop.id">{{ busyId === selectedWorkshop.id ? 'Guardando…' : 'Guardar cambios' }}</button><button type="button" class="table-action" :class="selectedWorkshop.is_active ? 'danger' : 'confirm'" :disabled="busyId === selectedWorkshop.id" @click="toggleStatus(selectedWorkshop)">{{ selectedWorkshop.is_active ? 'Deshabilitar taller' : 'Reactivar taller' }}</button></div></form><p v-else class="empty-state">Aún no tienes talleres registrados.</p></article>
    </section>
    <section class="form-card role-table-card"><div class="table-heading"><div><p class="eyebrow">EMPRESAS REGISTRADAS</p><h2>Mis talleres</h2></div><span class="table-count">{{ workshops.length }} registros</span></div><div v-if="workshops.length" class="role-table-wrap"><table class="role-table workshop-table"><thead><tr><th>Foto</th><th>Nombre comercial</th><th>RFC</th><th>Estado</th><th>Acciones</th></tr></thead><tbody><tr v-for="workshop in workshops" :key="workshop.id" :class="{ inactive: !workshop.is_active }" @click="chooseWorkshop(workshop)"><td><img v-if="workshop.photo_url" class="workshop-table-photo" :src="workshop.photo_url" :alt="`Foto de ${workshop.name}`" /><span v-else class="workshop-table-photo-empty" aria-label="Sin foto">—</span></td><td><strong>{{ workshop.name }}</strong><small>{{ workshop.state }} · {{ workshop.municipality }}</small></td><td><span class="rfc-value">{{ workshop.tax_id || 'Pendiente' }}</span><small>{{ workshop.postal_code ? `CP ${workshop.postal_code}` : 'Sin código postal' }}</small></td><td><span class="status-pill" :class="workshop.is_active ? 'active' : 'disabled'"><span class="status-dot"></span>{{ workshop.is_active ? 'Activo' : 'Deshabilitado' }}</span></td><td class="action-cell"><button class="table-action" @click.stop="previewing = workshop">Visualizar</button><button class="table-action" @click.stop="chooseWorkshop(workshop)">Administrar</button></td></tr></tbody></table></div><div v-else class="empty-state table-empty">Crea tu primer taller para comenzar.</div><p class="no-delete-note"><span>⌁</span> Los talleres se deshabilitan para conservar su historial; no se eliminan físicamente.</p></section>
    <div v-if="previewing" class="modal-backdrop" role="presentation" @click.self="previewing = null"><section class="modal-card workshop-preview-modal" role="dialog" aria-modal="true" aria-labelledby="workshop-preview-title"><div class="modal-heading"><div><p class="eyebrow">DETALLE DEL TALLER</p><h2 id="workshop-preview-title">{{ previewing.name }}</h2></div><button type="button" class="modal-close" aria-label="Cerrar detalle" @click="previewing = null">×</button></div><div class="workshop-preview-photo"><img v-if="previewing.photo_url" :src="previewing.photo_url" :alt="`Foto de ${previewing.name}`" /><div v-else class="workshop-photo-empty">Este taller todavía no tiene foto.</div></div><div class="workshop-preview-data"><div><span>Nombre comercial</span><strong>{{ previewing.name }}</strong></div><div><span>RFC</span><strong>{{ previewing.tax_id || 'Pendiente' }}</strong></div><div><span>Estado</span><strong>{{ previewing.state || 'Pendiente' }}</strong></div><div><span>Municipio o alcaldía</span><strong>{{ previewing.municipality || 'Pendiente' }}</strong></div><div><span>Localidad</span><strong>{{ previewing.locality || 'Sin localidad' }}</strong></div><div><span>Colonia</span><strong>{{ previewing.colony || 'Pendiente' }}</strong></div><div><span>Código postal</span><strong>{{ previewing.postal_code || 'Pendiente' }}</strong></div><div><span>Estado operativo</span><strong>{{ previewing.is_active ? 'Activo' : 'Deshabilitado' }}</strong></div></div><div class="modal-actions"><button type="button" class="secondary" @click="previewing = null">Cerrar</button><button type="button" class="primary" @click="chooseWorkshop(previewing); previewing = null">Administrar taller</button></div></section></div>
    <ConfirmationDialog :request="confirmation" :busy="confirmationBusy" @confirm="confirmPendingAction" @cancel="cancelPendingAction" />
  </main>
</template>
