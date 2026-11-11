<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import type { Customer, Vehicle } from '@/types'

const props = defineProps<{ customer: Customer }>()
const emit = defineEmits<{ notice: [kind: 'success' | 'error', text: string]; back: [] }>()
const vehicles = ref<Vehicle[]>([])
const loading = ref(false)
const busy = ref(false)
const systemVin = ref('Se generará al guardar')
const form = reactive({ vin: '', plate: '', brand: '', model: '', year: '', version: '', color: '', mileage: '' })
const photoInput = ref<HTMLInputElement | null>(null)
const photoPreview = ref('')
const photoName = ref('')
const photoError = ref('')
const photoReading = ref(false)
const maxYear = new Date().getFullYear() + 1
const maxPhotoBytes = 5 * 1024 * 1024

async function loadVehicles() {
  loading.value = true
  try { vehicles.value = await tallerMecanicoFacade.listVehicles(props.customer.workshop.id, props.customer.id) }
  catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar los vehículos.') }
  finally { loading.value = false }
}

function resetForm() {
  form.vin = ''; form.plate = ''; form.brand = ''; form.model = ''; form.year = ''; form.version = ''; form.color = ''; form.mileage = ''
  clearPhoto()
}

function clearPhoto() {
  photoPreview.value = ''
  photoName.value = ''
  photoError.value = ''
  if (photoInput.value) photoInput.value.value = ''
}

async function selectPhoto(event: Event) {
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
  photoReading.value = true
  try {
    photoPreview.value = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => typeof reader.result === 'string' ? resolve(reader.result) : reject(new Error('No se pudo leer la foto.'))
      reader.onerror = () => reject(new Error('No se pudo leer la foto seleccionada.'))
      reader.readAsDataURL(file)
    })
    photoName.value = file.name
  } catch (error) {
    photoError.value = error instanceof Error ? error.message : 'No se pudo leer la foto seleccionada.'
    input.value = ''
  } finally {
    photoReading.value = false
  }
}

async function saveVehicle() {
  if (!props.customer.is_active || photoError.value || photoReading.value) return
  busy.value = true
  try {
    const vehicle = await tallerMecanicoFacade.registerVehicle(props.customer.workshop.id, props.customer.id, {
      vin: form.vin,
      plate: form.plate,
      brand: form.brand,
      model: form.model,
      year: Number(form.year),
      version: form.version,
      color: form.color,
      mileage: form.mileage ? Number(form.mileage) : null,
    }, photoPreview.value || undefined)
    vehicles.value.unshift(vehicle)
    systemVin.value = vehicle.system_vin
    resetForm()
    emit('notice', 'success', 'Vehículo registrado y asociado al cliente correctamente.')
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo registrar el vehículo.') }
  finally { busy.value = false }
}

onMounted(loadVehicles)
</script>

<template>
  <main class="dashboard roles-page vehicle-page">
    <section class="dashboard-title roles-heading"><p class="eyebrow">CLIENTES / VEHÍCULOS</p><h1>Registrar vehículo.</h1><p>Asocia un automóvil a un cliente activo y conserva sus datos técnicos.</p></section>
    <section class="vehicle-context"><button type="button" class="secondary" @click="emit('back')">← Volver a clientes</button><div><span class="eyebrow">CLIENTE ASOCIADO</span><strong>{{ customer.full_name }}</strong><small>{{ customer.phone }} · {{ customer.email }}</small></div><div><span class="eyebrow">TALLER</span><strong>{{ customer.workshop.name }}</strong><small>{{ customer.workshop.state || 'Ubicación pendiente' }} · {{ customer.workshop.municipality || '' }}</small></div><span class="status-pill active"><span class="status-dot"></span>Cliente activo</span></section>
    <section class="vehicle-layout"><article class="form-card"><p class="eyebrow">NUEVO VEHÍCULO</p><h2>Datos del automóvil</h2><p>El VIN del sistema se genera automáticamente; el VIN del automóvil lo captura el usuario.</p><form @submit.prevent="saveVehicle"><label>VIN del sistema<input :value="systemVin" readonly aria-readonly="true" /><small>Identificador interno, no editable.</small></label><label>VIN del automóvil<input v-model.trim="form.vin" required minlength="17" maxlength="17" pattern="[A-HJ-NPR-Z0-9]{17}" placeholder="3VWFE21C04M000000" style="text-transform: uppercase" @input="form.vin = form.vin.toUpperCase().replace(/[^A-HJ-NPR-Z0-9]/g, '').slice(0, 17)" /><small>17 caracteres. No se permiten I, O ni Q.</small></label><div class="field-grid"><label>Placa<input v-model.trim="form.plate" required minlength="4" maxlength="10" pattern="[A-Za-z0-9-]{4,10}" placeholder="ABC-123" style="text-transform: uppercase" /></label><label>Marca<input v-model.trim="form.brand" required minlength="2" placeholder="Nissan" /></label><label>Modelo<input v-model.trim="form.model" required placeholder="Versa" /></label><label>Año<input v-model.number="form.year" required type="number" min="1886" :max="maxYear" placeholder="2024" /></label><label>Versión<input v-model.trim="form.version" required placeholder="Advance" /></label><label>Color<input v-model.trim="form.color" required placeholder="Blanco" /></label><label>Kilometraje <small>(opcional)</small><input v-model.number="form.mileage" type="number" min="0" step="1" placeholder="45000" /></label></div><div class="photo-upload-field"><label for="vehicle-photo">Foto del vehículo <small>(opcional)</small></label><input id="vehicle-photo" ref="photoInput" type="file" accept="image/jpeg,image/png,image/webp" aria-describedby="vehicle-photo-help" @change="selectPhoto" /><small id="vehicle-photo-help">JPG, PNG o WebP. Tamaño máximo: 5 MB.</small></div><div v-if="photoPreview" class="photo-selection"><img :src="photoPreview" alt="Vista previa de la foto del vehículo" /><div><strong>{{ photoName }}</strong><small>La foto se guardará con el vehículo asociado a este cliente.</small></div><button type="button" class="table-action danger" @click="clearPhoto">Quitar foto</button></div><p v-if="photoError" class="form-error" role="alert">{{ photoError }}</p><p class="vehicle-note">El técnico no se asigna durante este registro; la referencia técnica se agregará en el flujo correspondiente.</p><button class="primary" :disabled="busy || photoReading || !customer.is_active || !!photoError">{{ photoReading ? 'Preparando foto…' : busy ? 'Guardando…' : 'Registrar vehículo' }}</button></form></article><article class="form-card"><div class="table-heading"><div><p class="eyebrow">HISTORIAL DEL CLIENTE</p><h2>Vehículos asociados</h2></div><span class="table-count">{{ vehicles.length }} registros</span></div><div v-if="loading" class="empty-state table-empty">Cargando vehículos…</div><div v-else-if="vehicles.length" class="role-table-wrap"><table class="role-table vehicle-table"><thead><tr><th>Vehículo</th><th>Identificación</th><th>Detalles</th></tr></thead><tbody><tr v-for="vehicle in vehicles" :key="vehicle.id"><td><div class="vehicle-photo-cell"><img v-if="vehicle.photo_url" class="vehicle-photo-thumb" :src="vehicle.photo_url" :alt="`Foto de ${vehicle.brand} ${vehicle.model}`" /><span v-else class="vehicle-photo-empty">Sin foto</span><div class="vehicle-photo-copy"><strong>{{ vehicle.brand }} {{ vehicle.model }}</strong><small>{{ vehicle.version }} · {{ vehicle.color }}</small></div></div></td><td><strong>{{ vehicle.system_vin }}</strong><small>VIN: {{ vehicle.vin }} · Placa: {{ vehicle.plate }}</small></td><td><span>{{ vehicle.year }}</span><small>{{ vehicle.mileage === null ? 'Kilometraje no capturado' : `${vehicle.mileage.toLocaleString()} km` }}</small></td></tr></tbody></table></div><div v-else class="empty-state table-empty">Este cliente aún no tiene vehículos asociados.</div></article></section>
  </main>
</template>
