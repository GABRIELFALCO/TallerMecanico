<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { User, WorkshopAddress } from '@/types'
import { tallerMecanicoFacade } from '@/facades/TallerMecanicoFacade'
import WorkshopAddressFields from '@/components/WorkshopAddressFields.vue'

const emit = defineEmits<{ authenticated: [user: User]; notice: [kind: 'success' | 'error', text: string] }>()
const mode = ref<'login' | 'register'>('login')
const registerKind = ref<'workshop' | 'customer'>('workshop')
const busy = ref(false)
const login = reactive({ email: '', password: '' })
const emptyAddress = (): WorkshopAddress => ({ state: '', municipality: '', locality: '', colony: '', postal_code: '' })
const register = reactive({ fullName: '', workshopName: '', workshopTaxId: '', email: '', password: '', confirmation: '', address: emptyAddress() })
const customerRegister = reactive({ fullName: '', workshopTaxId: '', email: '', password: '', confirmation: '' })
const registerStep = computed(() => {
  if (!register.fullName.trim() || !register.workshopName.trim() || !register.workshopTaxId.trim()) return 1
  return Object.values(register.address).every((value) => value.trim()) ? 3 : 2
})

async function submitLogin() {
  busy.value = true
  try {
    const user = await tallerMecanicoFacade.signIn(login.email, login.password)
    emit('authenticated', user)
    emit('notice', 'success', `Bienvenido de nuevo, ${user.full_name}.`)
  } catch (error) {
    emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo iniciar sesión.')
  } finally { busy.value = false }
}

function showRecoveryPlaceholder() {
  emit('notice', 'success', 'La recuperación de contraseña estará disponible próximamente.')
}

async function submitRegister() {
  if (register.password !== register.confirmation) {
    emit('notice', 'error', 'Las contraseñas no coinciden.')
    return
  }
  busy.value = true
  try {
    const user = await tallerMecanicoFacade.createAccount(register.fullName, register.email, register.password, register.workshopName, register.workshopTaxId, register.address)
    emit('authenticated', user)
    emit('notice', 'success', 'Cuenta y taller creados correctamente. Ya puedes comenzar.')
  } catch (error) {
    emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo crear la cuenta.')
  } finally { busy.value = false }
}

async function submitCustomerRegister() {
  if (customerRegister.password !== customerRegister.confirmation) {
    emit('notice', 'error', 'Las contraseñas no coinciden.')
    return
  }
  busy.value = true
  try {
    const user = await tallerMecanicoFacade.createCustomerAccount(customerRegister.fullName, customerRegister.email, customerRegister.password, customerRegister.workshopTaxId)
    emit('authenticated', user)
    emit('notice', 'success', 'Acceso de cliente creado correctamente.')
  } catch (error) {
    emit('notice', 'error', error instanceof Error ? error.message : 'No se pudo crear el acceso de cliente.')
  } finally { busy.value = false }
}

async function submitRegistration() {
  if (registerKind.value === 'customer') await submitCustomerRegister()
  else await submitRegister()
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
          <div class="login-support"><button type="button" class="recovery-link" @click="showRecoveryPlaceholder">¿Olvidaste tu contraseña?</button></div>
          <button class="primary" :disabled="busy">{{ busy ? 'Validando…' : 'Entrar al sistema' }}</button>
        </form>
        <form v-else @submit.prevent="submitRegistration">
          <div class="registration-mode" role="group" aria-label="Tipo de cuenta"><button type="button" :class="{ active: registerKind === 'workshop' }" @click="registerKind = 'workshop'">Cuenta de taller</button><button type="button" :class="{ active: registerKind === 'customer' }" @click="registerKind = 'customer'">Soy cliente</button></div>
          <div v-if="registerKind === 'workshop'">
            <h2>Abre tu operación</h2><p>Crea tu cuenta y el primer taller.</p>
            <div class="creation-progress" aria-label="Progreso de creación de cuenta y taller"><div :class="{ current: registerStep === 1, complete: registerStep > 1 }"><span>1</span><small>Cuenta y taller</small></div><i></i><div :class="{ current: registerStep === 2, complete: registerStep > 2 }"><span>2</span><small>Ubicación</small></div><i></i><div :class="{ current: registerStep === 3 }"><span>3</span><small>Confirmar</small></div></div>
            <div class="field-grid"><label>Tu nombre<input v-model.trim="register.fullName" required minlength="3" placeholder="Nombre completo" /></label><label>Nombre del taller<input v-model.trim="register.workshopName" required minlength="3" placeholder="Taller del Norte" /></label></div>
            <label>RFC del taller<input v-model.trim="register.workshopTaxId" required minlength="12" maxlength="13" pattern="[A-Za-zÑñ&]{3,4}[0-9]{6}[A-Za-z0-9]{3}" placeholder="ABC010203AB1" style="text-transform: uppercase" /><small>12 o 13 caracteres; se convertirá a mayúsculas.</small></label>
            <WorkshopAddressFields v-model="register.address" :locality-optional="true" @notice="(kind, text) => emit('notice', kind, text)" />
            <label>Correo electrónico<input v-model.trim="register.email" type="email" autocomplete="email" required placeholder="nombre@taller.com" /></label>
            <div class="field-grid"><label>Contraseña<input v-model="register.password" type="password" autocomplete="new-password" required minlength="12" placeholder="12 caracteres mínimo" /></label><label>Confirmar contraseña<input v-model="register.confirmation" type="password" autocomplete="new-password" required placeholder="Repite tu contraseña" /></label></div>
            <button class="primary" :disabled="busy">{{ busy ? 'Creando…' : 'Crear cuenta y taller' }}</button>
          </div>
          <div v-else>
            <h2>Activa tu acceso de cliente</h2><p>Usa los datos con los que el taller registró tu ficha.</p>
            <label>Nombre completo<input v-model.trim="customerRegister.fullName" required minlength="5" pattern="[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+" placeholder="Nombre y apellidos" /></label>
            <label>RFC del taller<input v-model.trim="customerRegister.workshopTaxId" required minlength="12" maxlength="13" pattern="[A-Za-zÑñ&]{3,4}[0-9]{6}[A-Za-z0-9]{3}" placeholder="ABC010203AB1" style="text-transform: uppercase" /><small>Usa el RFC del mismo taller donde registraron tu ficha.</small></label>
            <label>Correo electrónico<input v-model.trim="customerRegister.email" type="email" autocomplete="email" required placeholder="El correo registrado por el taller" /></label>
            <div class="field-grid"><label>Contraseña<input v-model="customerRegister.password" type="password" autocomplete="new-password" required minlength="12" placeholder="12 caracteres mínimo" /></label><label>Confirmar contraseña<input v-model="customerRegister.confirmation" type="password" autocomplete="new-password" required placeholder="Repite tu contraseña" /></label></div>
            <p class="auth-help">Debe existir una ficha activa con el mismo nombre y correo en ese taller. El correo se compara sin distinguir mayúsculas; no se crea un registro duplicado.</p>
            <button class="primary" :disabled="busy">{{ busy ? 'Creando…' : 'Crear acceso de cliente' }}</button>
          </div>
        </form>
      </div>
    </section>
  </main>
</template>
