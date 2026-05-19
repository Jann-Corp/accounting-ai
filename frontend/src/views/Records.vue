<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRecordStore } from '@/stores/record'
import { useWalletStore } from '@/stores/wallet'
import { useCategoryStore } from '@/stores/category'
import { RecordType } from '@/types'
import type { RecordStatus } from '@/types'
import RecordModal from '@/components/RecordModal.vue'

const recordStore = useRecordStore()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()

const showModal = ref(false)
const showRecordModal = ref(false)
const editingRecord = ref<any>(null)
const filterType = ref<RecordType | ''>('')
const filterStatus = ref<RecordStatus | ''>('')

const form = ref({
  wallet_id: 0,
  category_id: null as number | null,
  amount: 0,
  record_type: 'expense' as RecordType,
  note: '',
  date: new Date().toISOString().slice(0, 16),
})

const filteredRecords = computed(() => {
  let records = recordStore.records
  if (filterType.value) {
    records = records.filter(r => r.record_type === filterType.value)
  }
  if (filterStatus.value) {
    records = records.filter(r => r.status === filterStatus.value)
  }
  return records
})

onMounted(async () => {
  await Promise.all([
    recordStore.fetchRecords({ limit: 100 }),
    walletStore.fetchWallets(),
    categoryStore.fetchCategories(),
  ])
})

function openAddModal() {
  editingRecord.value = null
  form.value = {
    wallet_id: walletStore.wallets[0]?.id || 0,
    category_id: null,
    amount: 0,
    record_type: RecordType.EXPENSE,
    note: '',
    date: new Date().toISOString().slice(0, 16),
  }
  showModal.value = true
}

function openEditModal(record: any) {
  editingRecord.value = record
  form.value = {
    wallet_id: record.wallet_id,
    category_id: record.category_id,
    amount: record.amount,
    record_type: record.record_type,
    note: record.note,
    date: record.date.slice(0, 16),
  }
  showModal.value = true
}

async function handleSubmit() {
  const data = {
    ...form.value,
    date: new Date(form.value.date).toISOString(),
  }
  if (editingRecord.value) {
    await recordStore.updateRecord(editingRecord.value.id, data)
  } else {
    await recordStore.createRecord(data)
  }
  showModal.value = false
}

async function handleDelete(id: number) {
  if (confirm('确定要删除这条记录吗？')) {
    await recordStore.deleteRecord(id)
  }
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(amount)
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex justify-between items-center">
      <h1 class="text-5xl font-semibold text-gray-900 tracking-tight">流水</h1>
      <button
        @click="showRecordModal = true"
        class="bg-gray-900 text-white px-8 py-3.5 rounded-full hover:opacity-85 font-medium text-sm"
      >
        记一笔
      </button>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 border border-gray-100 bg-white rounded-2xl p-4">
      <select v-model="filterType" class="border border-gray-100 rounded-full px-5 py-2.5 text-sm text-gray-600 bg-white">
        <option value="">全部类型</option>
        <option value="expense">支出</option>
        <option value="income">收入</option>
      </select>
      <select v-model="filterStatus" class="border border-gray-100 rounded-full px-5 py-2.5 text-sm text-gray-600 bg-white">
        <option value="">全部状态</option>
        <option value="confirmed">已确认</option>
        <option value="pending">待确认</option>
      </select>
    </div>

    <!-- Records List -->
    <div class="border border-gray-100 bg-white rounded-2xl overflow-hidden">
      <div v-if="filteredRecords.length === 0" class="text-center py-16 text-gray-400">
        <p>暂无记录</p>
      </div>
      <div v-else class="divide-y divide-gray-100">
        <div
          v-for="record in filteredRecords"
          :key="record.id"
          class="p-6 hover:bg-gray-50 flex items-center justify-between transition-colors"
        >
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center text-2xl">
              {{ record.category_icon || '📦' }}
            </div>
            <div>
              <p class="font-semibold text-gray-900 text-sm">{{ record.note || record.category_name || '未分类' }}</p>
              <p class="text-xs text-gray-500 mt-1">
                {{ record.wallet_name }} · {{ formatDate(record.date) }}
                <span v-if="record.status === 'pending'" class="text-gray-400 ml-1">· 待确认</span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <span :class="['font-semibold text-lg', record.record_type === 'expense' ? 'text-red-500' : 'text-emerald-600']">
              {{ record.record_type === 'expense' ? '-' : '+' }}{{ formatCurrency(record.amount) }}
            </span>
            <div class="flex gap-1">
              <button @click="openEditModal(record)" class="p-2 text-gray-400 hover:text-gray-900 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button @click="handleDelete(record.id)" class="p-2 text-gray-400 hover:text-red-500 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="border border-gray-100 bg-white rounded-2xl p-8 w-full max-w-md">
        <h2 class="text-2xl font-semibold text-gray-900 mb-6 tracking-tight">{{ editingRecord ? '编辑记录' : '添加记录' }}</h2>
        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">类型</label>
            <select v-model="form.record_type" class="w-full border border-gray-100 rounded-full px-4 py-3 bg-white text-gray-600">
              <option value="expense">支出</option>
              <option value="income">收入</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">金额</label>
            <input v-model.number="form.amount" type="number" step="0.01" class="w-full border border-gray-100 rounded-full px-4 py-3 bg-white text-gray-900" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">账户</label>
            <select v-model="form.wallet_id" class="w-full border border-gray-100 rounded-full px-4 py-3 bg-white text-gray-600" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">分类</label>
            <select v-model="form.category_id" class="w-full border border-gray-100 rounded-full px-4 py-3 bg-white text-gray-600">
              <option :value="null">未分类</option>
              <option v-for="c in categoryStore.categories" :key="c.id" :value="c.id">
                {{ c.icon }} {{ c.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">备注</label>
            <input v-model="form.note" type="text" class="w-full border border-gray-100 rounded-full px-4 py-3 bg-white text-gray-900" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">日期</label>
            <input v-model="form.date" type="datetime-local" class="w-full border border-gray-100 rounded-full px-4 py-3 bg-white text-gray-900" required />
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-3 border border-gray-200 rounded-full text-gray-700 hover:bg-gray-50 transition-colors">取消</button>
            <button type="submit" class="flex-1 py-3 bg-gray-900 text-white rounded-full hover:opacity-85 transition-opacity">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Record Modal -->
  <RecordModal :show="showRecordModal" @close="showRecordModal = false" />
</template>
