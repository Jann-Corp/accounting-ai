import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api'
import type { User, LoginRequest, RegisterRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  async function login(data: LoginRequest) {
    loading.value = true
    try {
      const res = await authApi.login(data)
      token.value = res.data.access_token
      await fetchUser(res.data.access_token)
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest) {
    loading.value = true
    try {
      await authApi.register(data)
      await login(data)
    } finally {
      loading.value = false
    }
  }

  async function fetchUser(accessToken?: string) {
    const tok = accessToken || token.value
    if (!tok) return
    try {
      const res = await authApi.getMe()
      user.value = res.data
    } catch {
      logout()
    }
  }

  async function updateDefaultWallet(walletId: number | null) {
    try {
      const res = await authApi.updateMe({ default_wallet_id: walletId })
      user.value = res.data
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || '更新失败')
    }
  }

  function logout() {
    authApi.logout()
    user.value = null
    token.value = null
  }

  // Initialize
  if (token.value) {
    fetchUser()
  }

  return { user, token, loading, login, register, logout, fetchUser, updateDefaultWallet }
})
