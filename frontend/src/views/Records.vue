<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRecordStore } from '@/stores/record'
import { useWalletStore } from '@/stores/wallet'
import { useCategoryStore } from '@/stores/category'
import { RecordType } from '@/types'
import type { RecordStatus } from '@/types'

const recordStore = useRecordStore()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()

const showModal = ref(false)
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
    <!-- Header -->
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold" style="color: var(--text-primary);">📝 记账记录</h1>
      <button @click="openAddModal" class="btn-gold">
        + 添加记录
      </button>
    </div>

    <!-- Filters -->
    <div
      class="flex gap-4 p-4 rounded-xl"
      style="background: var(--bg-card); border: 1px solid var(--border-color);"
    >
      <select
        v-model="filterType"
        class="flex-1"
        style="background: var(--bg-secondary); border: 1.5px solid var(--border-color); border-radius: 10px; color: var(--text-primary); padding: 8px 12px;"
      >
        <option value="">全部类型</option>
        <option value="expense">支出</option>
        <option value="income">收入</option>
      </select>
      <select
        v-model="filterStatus"
        class="flex-1"
        style="background: var(--bg-secondary); border: 1.5px solid var(--border-color); border-radius: 10px; color: var(--text-primary); padding: 8px 12px;"
      >
        <option value="">全部状态</option>
        <option value="confirmed">已确认</option>
        <option value="pending">待确认</option>
      </select>
    </div>

    <!-- Records List -->
    <div
      class="rounded-2xl overflow-hidden"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
    >
      <div v-if="filteredRecords.length === 0" class="text-center py-12" style="color: var(--text-muted);">
       暂无记录
      </div>
      <div v-else>
        <div
          v-for="record in filteredRecords"
          :key="record.id"
          class="p-4 flex items-center justify-between transition cursor-pointer hover:bg-hover"
          style="border-bottom: 1px solid var(--border-color);"
          @click="openEditModal(record)"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">{{ record.category_icon || '📦' }}</span>
            <div>
              <p class="font-medium" style="color: var(--text-primary);">{{ record.note || record.category_name || '未分类' }}</p>
              <p class="text-xs" style="color: var(--text-muted);">
                {{ record.wallet_name }} · {{ formatDate(record.date) }}
                <span
                  v-if="record.status === 'pending'"
                  class="ml-1 px-1.5 py-0.5 rounded text-xs"
                  style="background: var(--accent-gold-light); color: var(--accent-gold);"
                >
                  待确认
                </span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span
              class="font-bold text-lg text-amount"
              :style="{ color: record.record_type === 'expense' ? 'var(--expense-color)' : 'var(--income-color)' }"
            >
              {{ record.record_type === 'expense' ? '-' : '+' }}{{ formatCurrency(record.amount) }}
            </span>
            <button
              @click.stop="handleDelete(record.id)"
              class="p-2 rounded-lg transition"
              style="color: var(--text-muted);"
              title="删除"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay"
      @click.self="showModal = false"
    >
      <div
        class="rounded-2xl p-6 w-full max-w-md"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);"
      >
        <h2 class="text-xl font-bold mb-6" style="color: var(--text-primary);">
          {{ editingRecord ? '✏️ 编辑记录' : '➕ 添加记录' }}
        </h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Type -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">类型</label>
            <select v-model="form.record_type" class="input-gold">
              <option value="expense">支出</option>
              <option value="income">收入</option>
            </select>
          </div>
          <!-- Amount -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">金额</label>
            <input
              v-model.number="form.amount"
              type="number"
              step="0.01"
              class="input-gold"
              placeholder="0.00"
              required
            />
          </div>
          <!-- Wallet -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">账户</label>
            <select v-model="form.wallet_id" class="input-gold" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <!-- Category -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">分类</label>
            <select v-model="form.category_id" class="input-gold">
              <option :value="null">未分类</option>
              <option v-for="c in categoryStore.categories" :key="c.id" :value="c.id">
                {{ c.icon }} {{ c.name }}
              </option>
            </select>
          </div>
          <!-- Note -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">备注</label>
            <input v-model="form.note" type="text" class="input-gold" placeholder="可选" />
          </div>
          <!-- Date -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">日期</label>
            <input v-model="form.date" type="datetime-local" class="input-gold" required />
          </div>
          <!-- Actions -->
          <div class="flex gap-3 pt-2">
            <button
              type="button"
              @click="showModal = false"
              class="flex-1 py-2.5 rounded-xl border transition"
              style="border-color: var(--border-color); color: var(--text-secondary);"
            >
              取消
            </button>
            <button type="submit" class="flex-1 btn-gold">
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
