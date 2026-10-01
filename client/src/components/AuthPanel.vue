<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { User } from '@/types'
import { api } from '@/api'

const emit = defineEmits<{ authenticated: [user: User]; notice: [kind: 'success' | 'error', text: string] }>()
const mode = ref<'login' | 'register'>('login')
const busy = ref(false)
const login = reactive({ email: '', password: '' })
const register = reactive({ fullName: '', workshopName: '', email: '', password: '', confirmation: '' })

async function submitLogin() {
  busy.value = true
  try {
    const user = await api.login(login.email, login.password)
    emit('authenticated', user)
    emit('notice', 'success', `Bienvenido de nuevo, ${user.full_name}.`)
  } catch (error) {
    emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo iniciar sesión.')
  } finally { busy.value = false }
}

async function submitRegister() {
  if (register.password !== register.confirmation) {
    emit('notice', 'error', 'Las contraseñas no coinciden.')
    return
  }
  busy.value = true
  try {
    const user = await api.register(register.fullName, register.email, register.password, register.workshopName)
    emit('authenticated', user)
    emit('notice', 'success', 'Cuenta y taller creados correctamente. Ya puedes comenzar.')
  } catch (error) {
    emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo crear la cuenta.')
  } finally { busy.value = false }
}
</script>

<template>
  <main class="auth-layout">
    <section class="brand-panel">
      <div class="brand-mark">TM</div>
      <p class="eyebrow">OPERACIÓN INTELIGENTE</p>
      <h1>Tu taller,<br><em>en orden.</em></h1>
      <p class="brand-copy">Gestiona cada negocio desde una sesión segura. Recepción, equipo y clientes siempre en su lugar.</p>
      <div class="security-note"><span>⌁</span> Contraseñas protegidas con Argon2id</div>
    </section>
    <section class="auth-card-wrap">
      <div class="auth-card">
        <div class="tab-list" role="tablist">
          <button :class="{ active: mode === 'login' }" @click="mode = 'login'">Iniciar sesión</button>
          <button :class="{ active: mode === 'register' }" @click="mode = 'register'">Crear cuenta</button>
        </div>
        <form v-if="mode === 'login'" @submit.prevent="submitLogin">
          <h2>Qué gusto verte</h2><p>Ingresa a tu espacio de trabajo.</p>
          <label>Correo electrónico<input v-model.trim="login.email" type="email" autocomplete="email" required placeholder="nombre@taller.com" /></label>
          <label>Contraseña<input v-model="login.password" type="password" autocomplete="current-password" required placeholder="Tu contraseña" /></label>
          <button class="primary" :disabled="busy">{{ busy ? 'Validando…' : 'Entrar al sistema' }}</button>
        </form>
        <form v-else @submit.prevent="submitRegister">
          <h2>Abre tu operación</h2><p>Crea tu cuenta y el primer taller.</p>
          <div class="field-grid"><label>Tu nombre<input v-model.trim="register.fullName" required minlength="3" placeholder="Nombre completo" /></label><label>Nombre del taller<input v-model.trim="register.workshopName" required minlength="3" placeholder="Taller del Norte" /></label></div>
          <label>Correo electrónico<input v-model.trim="register.email" type="email" autocomplete="email" required placeholder="nombre@taller.com" /></label>
          <div class="field-grid"><label>Contraseña<input v-model="register.password" type="password" autocomplete="new-password" required minlength="12" placeholder="12 caracteres mínimo" /></label><label>Confirmar contraseña<input v-model="register.confirmation" type="password" autocomplete="new-password" required placeholder="Repite tu contraseña" /></label></div>
          <button class="primary" :disabled="busy">{{ busy ? 'Creando…' : 'Crear cuenta y taller' }}</button>
        </form>
      </div>
    </section>
  </main>
</template>
