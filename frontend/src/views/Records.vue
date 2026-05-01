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
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">📝 记账记录</h1>
      <button
        @click="showRecordModal = true"
        class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2"
      >
        <span>✏️</span>
        <span>记一笔</span>
      </button>
    </div>

    <!-- Filters -->
    <div class="flex gap-4 bg-white p-4 rounded-lg">
      <select v-model="filterType" class="border rounded-lg px-3 py-2">
        <option value="">全部类型</option>
        <option value="expense">支出</option>
        <option value="income">收入</option>
      </select>
      <select v-model="filterStatus" class="border rounded-lg px-3 py-2">
        <option value="">全部状态</option>
        <option value="confirmed">已确认</option>
        <option value="pending">待确认</option>
      </select>
    </div>

    <!-- Records List -->
    <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
      <div v-if="filteredRecords.length === 0" class="text-center py-12 text-gray-500">
        暂无记录
      </div>
      <div v-else class="divide-y">
        <div
          v-for="record in filteredRecords"
          :key="record.id"
          class="p-4 hover:bg-gray-50 flex items-center justify-between"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">{{ record.category_icon || '📦' }}</span>
            <div>
              <p class="font-medium">{{ record.note || record.category_name || '未分类' }}</p>
              <p class="text-xs text-gray-500">
                {{ record.wallet_name }} · {{ formatDate(record.date) }}
                <span v-if="record.status === 'pending'" class="text-yellow-600 ml-1">· 待确认</span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span :class="['font-bold text-lg', record.record_type === 'expense' ? 'text-red-500' : 'text-green-500']">
              {{ record.record_type === 'expense' ? '-' : '+' }}{{ formatCurrency(record.amount) }}
            </span>
            <button @click="openEditModal(record)" class="p-2 text-gray-400 hover:text-indigo-600">✏️</button>
            <button @click="handleDelete(record.id)" class="p-2 text-gray-400 hover:text-red-600">🗑️</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">{{ editingRecord ? '编辑记录' : '添加记录' }}</h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">类型</label>
            <select v-model="form.record_type" class="w-full border rounded-lg px-3 py-2">
              <option value="expense">支出</option>
              <option value="income">收入</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">金额</label>
            <input v-model.number="form.amount" type="number" step="0.01" class="w-full border rounded-lg px-3 py-2" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">账户</label>
            <select v-model="form.wallet_id" class="w-full border rounded-lg px-3 py-2" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
            <select v-model="form.category_id" class="w-full border rounded-lg px-3 py-2">
              <option :value="null">未分类</option>
              <option v-for="c in categoryStore.categories" :key="c.id" :value="c.id">
                {{ c.icon }} {{ c.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">备注</label>
            <input v-model="form.note" type="text" class="w-full border rounded-lg px-3 py-2" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">日期</label>
            <input v-model="form.date" type="datetime-local" class="w-full border rounded-lg px-3 py-2" required />
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-2 border rounded-lg">取消</button>
            <button type="submit" class="flex-1 py-2 bg-indigo-600 text-white rounded-lg">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Record Modal -->
  <RecordModal :show="showRecordModal" @close="showRecordModal = false" />
</template>
