<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRecordStore } from '@/stores/record'
import { useWalletStore } from '@/stores/wallet'
import { useCategoryStore } from '@/stores/category'
import { RecordType } from '@/types'
import type { RecordStatus } from '@/types'
import RecordModal from '@/components/RecordModal.vue'
import { formatDateOnly } from '@/utils/date'

const recordStore = useRecordStore()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()

const showModal = ref(false)
const showRecordModal = ref(false)
const editingRecord = ref<any>(null)
const filterType = ref<RecordType | ''>('')
const filterStatus = ref<RecordStatus | ''>('')

// 监听弹窗状态，阻止背景滚动
watch(showModal, (val) => {
  if (val) {
    // 禁止背景滚动
    document.body.style.overflow = 'hidden'
  } else {
    // 恢复背景滚动
    document.body.style.overflow = ''
  }
})

// iOS风格右滑删除状态
const swipedRecords = ref<Set<number>>(new Set())

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
    swipedRecords.value.delete(id)
  }
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(amount)
}

// iOS风格右滑删除（修复垂直滚动问题）
let touchStartX = 0
let touchStartY = 0
let currentTouchId = 0
let isHorizontalSwipe = false

function handleTouchStart(event: TouchEvent, recordId: number) {
  touchStartX = event.touches[0].clientX
  touchStartY = event.touches[0].clientY
  currentTouchId = recordId
  isHorizontalSwipe = false
}

function handleTouchMove(event: TouchEvent, recordId: number) {
  const touchX = event.touches[0].clientX
  const touchY = event.touches[0].clientY
  const deltaX = touchX - touchStartX
  const deltaY = touchY - touchStartY

  // 判断是否为水平滑动（水平移动距离大于垂直移动距离）
  if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
    isHorizontalSwipe = true
    // 阻止默认行为以启用右滑删除
    event.preventDefault()

    if (deltaX < -50) {
      // 向左滑动，显示删除按钮
      swipedRecords.value.add(recordId)
    } else if (deltaX > 50) {
      // 向右滑动，隐藏删除按钮
      swipedRecords.value.delete(recordId)
    }
  } else if (Math.abs(deltaY) > 10) {
    // 垂直滑动，允许默认滚动行为
    isHorizontalSwipe = false
  }
}

function handleTouchEnd(event: TouchEvent, recordId: number) {
  // 触摸结束时保持状态
  currentTouchId = 0
  isHorizontalSwipe = false
}

function resetSwipe(recordId: number) {
  // 点击其他区域时隐藏删除按钮
  if (currentTouchId !== recordId) {
    swipedRecords.value.delete(recordId)
  }
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
          class="relative group"
          @click="resetSwipe(record.id)"
        >
          <!-- 可滑动区域 -->
          <div
            class="p-6 hover:bg-gray-50 flex items-center justify-between transition-colors"
            @touchstart="handleTouchStart($event, record.id)"
            @touchmove="handleTouchMove($event, record.id)"
            @touchend="handleTouchEnd($event, record.id)"
          >
            <div class="flex items-center gap-4 flex-1 min-w-0">
              <div class="flex-shrink-0 w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center text-2xl">
                {{ record.category_icon || '📦' }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-gray-900 text-sm truncate">{{ record.note || record.category_name || '未分类' }}</p>
                <p class="text-xs text-gray-500 mt-1 truncate">
                  {{ record.wallet_name }} · {{ formatDateOnly(record.date) }}
                  <span v-if="record.status === 'pending'" class="text-gray-400 ml-1">· 待确认</span>
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4 flex-shrink-0 ml-3">
              <span :class="['font-semibold text-lg whitespace-nowrap', record.record_type === 'expense' ? 'text-red-500' : 'text-emerald-600']">
                {{ record.record_type === 'expense' ? '-' : '+' }}{{ formatCurrency(record.amount) }}
              </span>
              <div class="flex gap-1">
                <button @click.stop="openEditModal(record)" class="p-2 text-gray-400 hover:text-gray-900 transition-colors">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 右滑显示的删除按钮 (iOS风格) -->
          <div
            class="absolute right-0 top-0 bottom-0 w-20 bg-red-500 flex items-center justify-center text-white transition-transform duration-300 ease-in-out"
            :class="swipedRecords.has(record.id) ? 'translate-x-0' : 'translate-x-full'"
            @click.stop="handleDelete(record.id)"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="border border-gray-100 bg-white rounded-2xl p-8 w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col">
        <h2 class="text-2xl font-semibold text-gray-900 mb-6 tracking-tight flex-shrink-0">{{ editingRecord ? '编辑记录' : '添加记录' }}</h2>
        <form @submit.prevent="handleSubmit" class="space-y-5 flex-1 overflow-y-auto pr-1">
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
          <div class="flex gap-3 pt-2 flex-shrink-0">
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