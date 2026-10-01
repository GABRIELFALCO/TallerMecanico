<script setup lang="ts">
import type { Notice } from '@/types'

defineProps<{ notice: Notice | null }>()
</script>

<template>
  <Transition name="toast">
    <div v-if="notice" class="toast" :class="notice.kind" role="alert" aria-live="polite">
      <span>{{ notice.kind === 'success' ? '✓' : '!' }}</span>
      <p>{{ notice.text }}</p>
    </div>
  </Transition>
</template>
