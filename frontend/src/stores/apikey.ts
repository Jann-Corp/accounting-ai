import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiKeyApi } from '@/api'
import type { ApiKeyResponse, ApiKeyCreate } from '@/types'

export const useApiKeyStore = defineStore('apikey', () => {
  const apiKeys = ref<ApiKeyResponse[]>([])
  const loading = ref(false)

  async function fetchApiKeys() {
    loading.value = true
    try {
      const res = await apiKeyApi.list()
      apiKeys.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createApiKey(data: ApiKeyCreate) {
    const res = await apiKeyApi.create(data)
    apiKeys.value.unshift(res.data)
    return res.data
  }

  async function toggleApiKey(id: number, is_active: boolean) {
    const res = await apiKeyApi.update(id, { is_active })
    const idx = apiKeys.value.findIndex(k => k.id === id)
    if (idx !== -1) apiKeys.value[idx] = res.data
    return res.data
  }

  async function deleteApiKey(id: number) {
    await apiKeyApi.delete(id)
    apiKeys.value = apiKeys.value.filter(k => k.id !== id)
  }

  return {
    apiKeys,
    loading,
    fetchApiKeys,
    createApiKey,
    toggleApiKey,
    deleteApiKey,
  }
})
