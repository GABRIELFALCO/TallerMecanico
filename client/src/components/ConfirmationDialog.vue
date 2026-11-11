<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import type { ConfirmationRequest } from '@/types'

const props = defineProps<{ request: ConfirmationRequest | null; busy?: boolean }>()
const emit = defineEmits<{ confirm: []; cancel: [] }>()
const confirmButton = ref<HTMLButtonElement | null>(null)
const cancelButton = ref<HTMLButtonElement | null>(null)

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && !props.busy) emit('cancel')
}

watch(() => props.request, async (request) => {
  if (!request) return
  window.addEventListener('keydown', handleKeydown)
  await nextTick()
  if (request.variant === 'danger') cancelButton.value?.focus()
  else confirmButton.value?.focus()
}, { flush: 'post' })

watch(() => props.request, (request, previousRequest) => {
  if (!request && previousRequest) window.removeEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
</script>

<template>
  <div v-if="request" class="modal-backdrop confirmation-backdrop" role="presentation" @click.self="!busy && emit('cancel')">
    <section class="modal-card confirmation-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirmation-title" aria-describedby="confirmation-message">
      <div class="confirmation-dialog-heading">
        <span class="confirmation-symbol" :class="request.variant" aria-hidden="true">{{ request.variant === 'danger' ? '!' : '?' }}</span>
        <div>
          <p class="eyebrow">CONFIRMACIÓN</p>
          <h2 id="confirmation-title">{{ request.title }}</h2>
        </div>
        <button type="button" class="modal-close" aria-label="Cerrar confirmación" :disabled="busy" @click="emit('cancel')">×</button>
      </div>
      <p id="confirmation-message" class="confirmation-message">{{ request.message }}</p>
      <div class="confirmation-dialog-actions">
        <button ref="cancelButton" type="button" class="secondary" :disabled="busy" @click="emit('cancel')">Cancelar</button>
        <button ref="confirmButton" type="button" class="primary" :class="{ 'danger-action': request.variant === 'danger' }" :disabled="busy" @click="emit('confirm')">
          {{ busy ? 'Procesando…' : request.confirmLabel }}
        </button>
      </div>
    </section>
  </div>
</template>
