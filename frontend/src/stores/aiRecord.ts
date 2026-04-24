import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { aiApi } from '@/api'

interface PendingRecord {
  id: number
  amount: number
  record_type: 'expense' | 'income'
  note: string
  date: string
  category_id: number | null
  original_image_url: string
  ai_confidence: number
  is_ai_recognized: number
  is_suspected_duplicate: number
  job_id: number
  status: 'pending' | 'confirmed' | 'rejected'
  created_at: string
  updated_at: string
}

export const useAIRecordStore = defineStore('aiRecord', () => {
  const pendingRecords = ref<PendingRecord[]>([])
  const loading = ref(false)
  const lastFetchedAt = ref<number>(0)
  const hasViewedPending = ref(false)

  const hasPendingRecords = computed(() => pendingRecords.value.length > 0)
  const pendingCount = computed(() => pendingRecords.value.length)
  const showBadge = computed(() => hasPendingRecords.value && !hasViewedPending.value)

  async function fetchPendingRecords() {
    loading.value = true
    try {
      const res = await aiApi.listPendingRecords()
      const oldCount = pendingRecords.value.length
      pendingRecords.value = res.data
      
      // 如果有新增的待确认记录，重置 viewed 状态
      if (res.data.length > oldCount) {
        hasViewedPending.value = false
      }
      
      lastFetchedAt.value = Date.now()
    } finally {
      loading.value = false
    }
  }

  function markAsViewed() {
    hasViewedPending.value = true
  }

  async function confirmRecord(recordId: number) {
    await aiApi.confirmRecord(recordId)
    pendingRecords.value = pendingRecords.value.filter(r => r.id !== recordId)
  }

  async function rejectRecord(recordId: number) {
    await aiApi.rejectRecord(recordId)
    pendingRecords.value = pendingRecords.value.filter(r => r.id !== recordId)
  }

  return {
    pendingRecords,
    loading,
    hasPendingRecords,
    pendingCount,
    showBadge,
    fetchPendingRecords,
    markAsViewed,
    confirmRecord,
    rejectRecord,
  }
})
