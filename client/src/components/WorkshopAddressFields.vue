<script setup lang="ts">
import { computed, ref } from 'vue'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import type { PostalCodeLookup, WorkshopAddress } from '@/types'

const props = withDefaults(defineProps<{ modelValue: WorkshopAddress; localityOptional?: boolean }>(), { localityOptional: false })
const emit = defineEmits<{
  'update:modelValue': [value: WorkshopAddress]
  notice: [kind: 'success' | 'error', text: string]
}>()

const loading = ref(false)
const postalResult = ref<PostalCodeLookup | null>(null)

function updateField(field: keyof WorkshopAddress, value: string) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

function updateLocality(value: string) {
  const firstColony = value
    ? postalResult.value?.asentamientos.find((item) => item.ciudad === value)?.nombre ?? ''
    : props.modelValue.colony || (postalResult.value?.asentamientos[0]?.nombre ?? '')
  emit('update:modelValue', { ...props.modelValue, locality: value, colony: firstColony })
}

const localities = computed(() => [...new Set((postalResult.value?.asentamientos ?? []).map((item) => item.ciudad).filter(Boolean))])
const colonies = computed(() => {
  const settlements = postalResult.value?.asentamientos ?? []
  const filtered = settlements.filter((item) => !props.modelValue.locality || item.ciudad === props.modelValue.locality)
  return [...new Set(filtered.map((item) => item.nombre).filter(Boolean))]
})

async function searchPostalCode() {
  if (!/^\d{5}$/.test(props.modelValue.postal_code)) {
    emit('notice', 'error', 'Escribe un código postal válido de 5 dígitos.')
    return
  }
  loading.value = true
  try {
    const result = await tallerMecanicoFacade.lookupPostalCode(props.modelValue.postal_code)
    postalResult.value = result
    const firstLocality = localities.value[0] ?? ''
    const firstColony = result.asentamientos.find((item) => item.ciudad === firstLocality)?.nombre ?? result.asentamientos[0]?.nombre ?? ''
    emit('update:modelValue', {
      ...props.modelValue,
      postal_code: result.cp,
      state: result.estado,
      municipality: result.municipio,
      locality: firstLocality,
      colony: firstColony,
    })
    emit('notice', 'success', 'Ubicación encontrada. Revisa y selecciona localidad y colonia.')
  } catch (error) {
    postalResult.value = null
    emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo consultar el código postal.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <fieldset class="address-fields">
    <legend>Ubicación del taller</legend>
    <p class="address-help">Captura tu CP y te ayudaremos a completar el domicilio con datos postales oficiales.</p>
    <div class="postal-search">
      <label>Código postal<input :value="modelValue.postal_code" inputmode="numeric" autocomplete="postal-code" required minlength="5" maxlength="5" pattern="[0-9]{5}" placeholder="06600" @input="updateField('postal_code', ($event.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, 5))" /></label>
      <button type="button" class="secondary postal-button" :disabled="loading" @click="searchPostalCode">{{ loading ? 'Buscando…' : 'Buscar ubicación' }}</button>
    </div>
    <div class="field-grid address-grid">
      <label>Estado<select :value="modelValue.state" required :disabled="!postalResult" @change="updateField('state', ($event.target as HTMLSelectElement).value)"><option value="" disabled>Selecciona un estado</option><option v-if="modelValue.state" :value="modelValue.state">{{ modelValue.state }}</option></select></label>
      <label>Municipio o alcaldía<select :value="modelValue.municipality" required :disabled="!postalResult" @change="updateField('municipality', ($event.target as HTMLSelectElement).value)"><option value="" disabled>Selecciona un municipio</option><option v-if="modelValue.municipality" :value="modelValue.municipality">{{ modelValue.municipality }}</option></select></label>
      <label>Localidad <small v-if="localityOptional">(opcional)</small><select :value="modelValue.locality" :required="!localityOptional" :disabled="!postalResult" @change="updateLocality(($event.target as HTMLSelectElement).value)"><option value="">{{ localityOptional ? 'Sin localidad' : 'Selecciona una localidad' }}</option><option v-for="locality in localities" :key="locality" :value="locality">{{ locality }}</option></select></label>
      <label>Colonia<select :value="modelValue.colony" required :disabled="!postalResult" @change="updateField('colony', ($event.target as HTMLSelectElement).value)"><option value="" disabled>Selecciona una colonia</option><option v-for="colony in colonies" :key="colony" :value="colony">{{ colony }}</option></select></label>
    </div>
    <small class="address-source">La ubicación se consulta por código postal; puedes revisar cada selección antes de guardar.</small>
  </fieldset>
</template>
