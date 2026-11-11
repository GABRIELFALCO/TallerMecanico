<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import type { Vehicle, Workshop } from '@/types'

const emit = defineEmits<{ notice: [kind: 'success' | 'error', text: string] }>()
const workshops = ref<Workshop[]>([])
const vehicles = ref<Vehicle[]>([])
const selectedWorkshopId = ref('')
const loading = ref(false)
const selectedWorkshop = ref<Workshop | undefined>()

async function loadWorkshops() {
  try {
    workshops.value = (await tallerMecanicoFacade.listWorkshops()).filter((item) => item.role === 'customer' && item.is_active)
    selectedWorkshopId.value = workshops.value[0]?.id ?? ''
    await loadVehicles()
  } catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar tus talleres.') }
}

async function loadVehicles() {
  selectedWorkshop.value = workshops.value.find((item) => item.id === selectedWorkshopId.value)
  if (!selectedWorkshopId.value) { vehicles.value = []; return }
  loading.value = true
  try { vehicles.value = await tallerMecanicoFacade.listMyVehicles(selectedWorkshopId.value) }
  catch (error) { emit('notice', 'error', error instanceof Error ? error.message : 'No se pudieron cargar tus vehículos.') }
  finally { loading.value = false }
}

watch(selectedWorkshopId, loadVehicles)
onMounted(loadWorkshops)
</script>

<template>
  <main class="dashboard roles-page my-vehicles-page">
    <section class="dashboard-title roles-heading"><p class="eyebrow">MI INFORMACIÓN</p><h1>Mis vehículos.</h1><p>Consulta los vehículos asociados a tu cuenta y revisa su información registrada en el taller.</p></section>
    <section class="customer-toolbar form-card" v-if="workshops.length"><label>Taller<select v-model="selectedWorkshopId"><option v-for="workshop in workshops" :key="workshop.id" :value="workshop.id">{{ workshop.name }}</option></select></label><span class="selected-workshop">Cliente autorizado · {{ selectedWorkshop?.name }}</span></section>
    <section class="form-card role-table-card">
      <div class="table-heading">
        <div><p class="eyebrow">HISTORIAL PERSONAL</p><h2>Vehículos asociados</h2></div>
        <span class="table-count">{{ vehicles.length }} registros</span>
      </div>
      <div v-if="loading" class="empty-state table-empty">Cargando tus vehículos…</div>
      <div v-else-if="!workshops.length" class="empty-state table-empty">No tienes un taller activo asociado a tu cuenta de cliente.</div>
      <div v-else-if="vehicles.length" class="role-table-wrap">
        <table class="role-table my-vehicles-table" aria-label="Vehículos asociados a tu cuenta">
          <colgroup>
            <col class="my-vehicle-column" />
            <col class="vehicle-identity-column" />
            <col class="vehicle-details-column" />
            <col class="vehicle-status-column" />
          </colgroup>
          <thead>
            <tr><th>Vehículo</th><th>Identificación</th><th>Detalles</th><th>Estado</th></tr>
          </thead>
          <tbody>
            <tr v-for="vehicle in vehicles" :key="vehicle.id" :class="{ inactive: !vehicle.is_active }">
              <td>
                <div class="vehicle-photo-cell">
                  <img v-if="vehicle.photo_url" class="vehicle-photo-thumb" :src="vehicle.photo_url" :alt="`Foto de ${vehicle.brand} ${vehicle.model}`" />
                  <span v-else class="vehicle-photo-empty">Sin foto</span>
                  <div class="vehicle-photo-copy"><strong>{{ vehicle.brand }} {{ vehicle.model }}</strong><small>{{ vehicle.version }} · {{ vehicle.color }}</small></div>
                </div>
              </td>
              <td><div class="vehicle-table-stack"><strong>{{ vehicle.system_vin }}</strong><small>VIN: {{ vehicle.vin }} · Placa: {{ vehicle.plate }}</small></div></td>
              <td><div class="vehicle-table-stack"><span>Año {{ vehicle.year }}</span><small>{{ vehicle.mileage === null ? 'Kilometraje no capturado' : `${vehicle.mileage.toLocaleString()} km` }}</small></div></td>
              <td><span class="status-pill" :class="vehicle.is_active ? 'active' : 'disabled'"><span class="status-dot"></span>{{ vehicle.is_active ? 'Activo' : 'Deshabilitado' }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state table-empty">Aún no hay vehículos asociados a tu cuenta en este taller.</div>
    </section>
  </main>
</template>
