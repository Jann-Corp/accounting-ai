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
  // ========== 测试用：模拟数据 ==========
  const mockPendingRecords: PendingRecord[] = [
    {
      id: 1,
      amount: 25.50,
      record_type: 'expense',
      note: '午餐',
      date: new Date().toISOString(),
      category_id: null,
      original_image_url: '/test1.jpg',
      ai_confidence: 0.92,
      is_ai_recognized: 1,
      is_suspected_duplicate: 0,
      job_id: 1,
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 2,
      amount: 128.00,
      record_type: 'expense',
      note: '超市购物',
      date: new Date().toISOString(),
      category_id: null,
      original_image_url: '/test2.jpg',
      ai_confidence: 0.87,
      is_ai_recognized: 1,
      is_suspected_duplicate: 1,
      job_id: 2,
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 3,
      amount: 2000.00,
      record_type: 'income',
      note: '工资',
      date: new Date().toISOString(),
      category_id: null,
      original_image_url: '/test3.jpg',
      ai_confidence: 0.95,
      is_ai_recognized: 1,
      is_suspected_duplicate: 0,
      job_id: 3,
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]

  const pendingRecords = ref<PendingRecord[]>([])
  const loading = ref(false)
  const lastFetchedAt = ref<number>(0)
  const hasViewedPending = ref(false)

  // ========== 测试用：控制显示 ==========
  const useMockData = ref(true) // 开启测试模式

  const hasPendingRecords = computed(() => {
    if (useMockData.value) return true
    return pendingRecords.value.length > 0
  })

  const pendingCount = computed(() => {
    if (useMockData.value) return 3
    return pendingRecords.value.length
  })

  const showBadge = computed(() => hasPendingRecords.value && !hasViewedPending.value)

  async function fetchPendingRecords() {
    loading.value = true
    try {
      if (useMockData.value) {
        pendingRecords.value = [...mockPendingRecords]
      } else {
        const res = await aiApi.listPendingRecords()
        const oldCount = pendingRecords.value.length
        pendingRecords.value = res.data
        
        if (res.data.length > oldCount) {
          hasViewedPending.value = false
        }
      }
      lastFetchedAt.value = Date.now()
    } finally {
      loading.value = false
    }
  }

  function markAsViewed() {
    hasViewedPending.value = true
  }

  // 测试用：重置状态
  function resetForTest() {
    hasViewedPending.value = false
  }

  async function confirmRecord(recordId: number) {
    if (useMockData.value) {
      pendingRecords.value = pendingRecords.value.filter(r => r.id !== recordId)
    } else {
      await aiApi.confirmRecord(recordId)
      pendingRecords.value = pendingRecords.value.filter(r => r.id !== recordId)
    }
  }

  async function rejectRecord(recordId: number) {
    if (useMockData.value) {
      pendingRecords.value = pendingRecords.value.filter(r => r.id !== recordId)
    } else {
      await aiApi.rejectRecord(recordId)
      pendingRecords.value = pendingRecords.value.filter(r => r.id !== recordId)
    }
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
    // 测试用
    useMockData,
    resetForTest,
  }
})
