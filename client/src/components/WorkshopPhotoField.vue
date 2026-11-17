<script setup lang="ts">
import { ref } from 'vue'

const model = defineModel<string>()
const emit = defineEmits<{ error: [message: string] }>()
const error = ref('')
let selection = 0

async function selectPhoto(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  const current = ++selection
  model.value = undefined
  error.value = ''
  if (file) {
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) error.value = 'Elige una imagen JPG, PNG o WebP.'
    else if (file.size > 5 * 1024 * 1024) error.value = 'La foto no debe superar los 5 MB.'
    else {
      emit('error', 'Espera a que termine de cargar la foto.')
      try {
        const data = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => typeof reader.result === 'string' ? resolve(reader.result) : reject()
          reader.onerror = () => reject()
          reader.readAsDataURL(file)
        })
        if (current !== selection) return
        model.value = data
      } catch {
        if (current !== selection) return
        error.value = 'No se pudo leer la foto seleccionada.'
      }
    }
  }
  emit('error', error.value)
}
</script>

<template>
  <label class="photo-upload-field">Agregar o reemplazar foto <small>(opcional)</small>
    <input type="file" accept="image/jpeg,image/png,image/webp" @change="selectPhoto" />
    <small>JPG, PNG o WebP; máximo 5 MB. Si no eliges una foto, se conserva la actual.</small>
  </label>
  <p v-if="error" class="form-error" role="alert">{{ error }}</p>
  <div v-if="model" class="photo-selection"><img :src="model" alt="Vista previa de la nueva foto del taller" /></div>
</template>
