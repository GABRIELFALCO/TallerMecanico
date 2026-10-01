<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, ApiError } from '@/api'
import AuthPanel from '@/components/AuthPanel.vue'
import DashboardPanel from '@/components/DashboardPanel.vue'
import ToastMessage from '@/components/ToastMessage.vue'
import type { Notice, User } from '@/types'

const user = ref<User | null>(null)
const loading = ref(true)
const notice = ref<Notice | null>(null)
let noticeTimer: ReturnType<typeof setTimeout> | undefined

function showNotice(kind: Notice['kind'], text: string) {
  notice.value = { kind, text }
  if (noticeTimer) clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => { notice.value = null }, 5000)
}

onMounted(async () => {
  try { user.value = await api.me() }
  catch (error) { if (!(error instanceof ApiError && error.status === 401)) showNotice('error', error instanceof Error ? error.message : 'No se pudo comprobar la sesión.') }
  finally { loading.value = false }
})
</script>

<template>
  <div v-if="loading" class="page-loader"><span></span><p>Preparando tu espacio de trabajo…</p></div>
  <DashboardPanel v-else-if="user" :user="user" @logout="user = null" @notice="showNotice" />
  <AuthPanel v-else @authenticated="user = $event" @notice="showNotice" />
  <ToastMessage :notice="notice" />
</template>
