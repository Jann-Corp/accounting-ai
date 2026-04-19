import { defineStore } from 'pinia'
import { ref } from 'vue'
import { recordApi } from '@/api'
import type { Record, RecordCreate, RecordType, RecordStatus } from '@/types'

export const useRecordStore = defineStore('record', () => {
  const records = ref<Record[]>([])
  const pendingRecords = ref<Record[]>([])
  const loading = ref(false)

  async function fetchRecords(params?: {
    start_date?: string
    end_date?: string
    wallet_id?: number
    category_id?: number
    record_type?: RecordType
    status?: RecordStatus
    limit?: number
    offset?: number
  }) {
    loading.value = true
    try {
      const res = await recordApi.list(params)
      records.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchPending() {
    const res = await recordApi.pending()
    pendingRecords.value = res.data
  }

  async function createRecord(data: RecordCreate) {
    const res = await recordApi.create(data)
    records.value.unshift(res.data)
    return res.data
  }

  async function updateRecord(id: number, data: Partial<RecordCreate>) {
    const res = await recordApi.update(id, data)
    const idx = records.value.findIndex(r => r.id === id)
    if (idx !== -1) records.value[idx] = res.data
    return res.data
  }

  async function deleteRecord(id: number) {
    await recordApi.delete(id)
    records.value = records.value.filter(r => r.id !== id)
  }

  async function confirmRecord(id: number) {
    const res = await recordApi.confirm(id)
    pendingRecords.value = pendingRecords.value.filter(r => r.id !== id)
    const idx = records.value.findIndex(r => r.id === id)
    if (idx !== -1) records.value[idx] = res.data
  }

  async function rejectRecord(id: number) {
    await recordApi.reject(id)
    pendingRecords.value = pendingRecords.value.filter(r => r.id !== id)
  }

  return {
    records,
    pendingRecords,
    loading,
    fetchRecords,
    fetchPending,
    createRecord,
    updateRecord,
    deleteRecord,
    confirmRecord,
    rejectRecord,
  }
})
