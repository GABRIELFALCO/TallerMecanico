<script setup lang="ts">
import { computed } from 'vue'
import type { Notice } from '@/types'

const props = defineProps<{ notice: Notice | null }>()
const emit = defineEmits<{ dismiss: [] }>()
const duration = computed(() => `${props.notice?.durationMs ?? 5000}ms`)
</script>

<template>
  <Transition name="toast">
    <div
      v-if="notice"
      class="toast"
      :class="notice.kind"
      :role="notice.kind === 'error' ? 'alert' : 'status'"
      :aria-live="notice.kind === 'error' ? 'assertive' : 'polite'"
      :style="{ '--toast-duration': duration }"
    >
      <span class="toast-icon" aria-hidden="true">{{ notice.kind === 'success' ? '✓' : '!' }}</span>
      <div class="toast-content">
        <strong>{{ notice.kind === 'success' ? 'Listo' : 'Revisa esta operación' }}</strong>
        <p>{{ notice.text }}</p>
      </div>
      <button type="button" class="toast-close" aria-label="Cerrar aviso" @click="emit('dismiss')">×</button>
      <span class="toast-progress" aria-hidden="true"></span>
    </div>
  </Transition>
</template>
