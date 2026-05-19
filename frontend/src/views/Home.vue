<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWalletStore } from '@/stores/wallet'
import { useRecordStore } from '@/stores/record'
import { useCategoryStore } from '@/stores/category'
import { useAuthStore } from '@/stores/auth'
import { useAIRecordStore } from '@/stores/aiRecord'
import { statsApi } from '@/api'
import type { MonthlyStats, CategoryBreakdown } from '@/types'
import RecordModal from '@/components/RecordModal.vue'

const router = useRouter()
const walletStore = useWalletStore()
const recordStore = useRecordStore()
const categoryStore = useCategoryStore()
const authStore = useAuthStore()
const aiRecordStore = useAIRecordStore()

const monthlyStats = ref<MonthlyStats | null>(null)
const categoryBreakdown = ref<CategoryBreakdown[]>([])
const recentRecords = computed(() => recordStore.records.slice(0, 5))
const showRecordModal = ref(false)

const currentMonth = new Date().toLocaleString('zh-CN', { year: 'numeric', month: 'long' })

onMounted(async () => {
  await Promise.all([
    walletStore.fetchWallets(),
    recordStore.fetchRecords({ limit: 5 }),
    categoryStore.fetchCategories(),
    aiRecordStore.fetchPendingRecords(),
  ])
  try {
    const [statsRes, breakdownRes] = await Promise.all([
      statsApi.monthly(),
      statsApi.categoryBreakdown(),
    ])
    monthlyStats.value = statsRes.data
    categoryBreakdown.value = breakdownRes.data.breakdown.slice(0, 6)
  } catch (e) {
    console.error('Failed to load stats', e)
  }
})

function goToAIRecords() {
  aiRecordStore.markAsViewed()
  router.push('/ai-records')
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(amount)
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' })
}
</script>

<template>
  <div class="space-y-8">
    <!-- Hero Section -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 py-4">
      <div class="flex-1">
        <h1 class="text-5xl sm:text-6xl font-medium text-gray-900 tracking-tight mb-2" style="letter-spacing: -0.8px;">
          你好，{{ authStore.user?.username || '用户' }}
        </h1>
        <p class="text-lg text-gray-500 font-normal" style="letter-spacing: 0.24px;">{{ currentMonth }}</p>
      </div>
      <button
        @click="showRecordModal = true"
        class="px-8 py-3.5 bg-gray-900 text-white rounded-full font-medium hover:opacity-85 transition-opacity text-base"
      >
        记一笔
      </button>
    </div>

    <!-- Balance Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
      <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <p class="text-sm text-gray-500 font-medium mb-3" style="letter-spacing: 0.16px;">总资产</p>
        <p class="text-4xl font-medium text-gray-900 tracking-tight" style="letter-spacing: -0.32px;">
          {{ formatCurrency(walletStore.totalBalance) }}
        </p>
      </div>
      <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <p class="text-sm text-gray-500 font-medium mb-3" style="letter-spacing: 0.16px;">本月收入</p>
        <p class="text-4xl font-medium text-emerald-600 tracking-tight" style="letter-spacing: -0.32px;">
          {{ formatCurrency(monthlyStats?.total_income || 0) }}
        </p>
      </div>
      <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <p class="text-sm text-gray-500 font-medium mb-3" style="letter-spacing: 0.16px;">本月支出</p>
        <p class="text-4xl font-medium text-red-500 tracking-tight" style="letter-spacing: -0.32px;">
          {{ formatCurrency(monthlyStats?.total_expense || 0) }}
        </p>
      </div>
    </div>

    <!-- Accounts Overview -->
    <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-medium text-gray-900 tracking-tight" style="letter-spacing: -0.4px;">我的账户</h2>
        <router-link to="/wallets" class="text-blue-500 text-sm font-medium hover:underline" style="letter-spacing: 0.16px;">
          管理
        </router-link>
      </div>
      <div v-if="walletStore.wallets.length === 0" class="text-center py-12">
        <p class="text-gray-500 mb-4 text-base" style="letter-spacing: 0.24px;">还没有账户</p>
        <router-link to="/wallets" class="inline-block px-6 py-3 bg-gray-100 text-gray-900 rounded-full font-medium hover:opacity-85 transition-opacity text-sm">
          创建账户
        </router-link>
      </div>
      <div v-else class="space-y-4">
        <div
          v-for="wallet in walletStore.wallets"
          :key="wallet.id"
          class="flex justify-between items-center p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
        >
          <div class="flex items-center gap-4">
            <span class="text-3xl">
              {{ wallet.wallet_type === 'cash' ? '💵' : wallet.wallet_type === 'bank_card' ? '🏦' : wallet.wallet_type === 'e_wallet' ? '💳' : '💳' }}
            </span>
            <span class="text-base font-medium text-gray-900" style="letter-spacing: 0.24px;">{{ wallet.name }}</span>
          </div>
          <span :class="['text-xl font-medium', wallet.balance >= 0 ? 'text-emerald-600' : 'text-red-500']" style="letter-spacing: -0.32px;">
            {{ formatCurrency(wallet.balance) }}
          </span>
        </div>
      </div>
    </div>

    <!-- AI Records Entry -->
    <div v-if="aiRecordStore.hasPendingRecords" class="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl border-2 border-amber-200 overflow-hidden">
      <button
        @click="goToAIRecords"
        class="w-full p-6 flex items-center justify-between hover:from-amber-100 hover:to-orange-100 transition-colors"
      >
        <div class="flex items-center gap-5">
          <div class="w-14 h-14 bg-amber-400 rounded-full flex items-center justify-center relative">
            <span class="text-3xl">🤖</span>
            <span
              v-if="aiRecordStore.showBadge"
              class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full animate-pulse border-2 border-white"
            />
          </div>
          <div class="text-left">
            <h3 class="text-lg font-medium text-gray-900" style="letter-spacing: -0.24px;">有待确认的 AI 识别记录</h3>
            <p class="text-sm text-gray-500 mt-1" style="letter-spacing: 0.16px;">
              共 {{ aiRecordStore.pendingCount }} 条记录待确认
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="bg-amber-400 text-gray-900 text-sm font-bold px-4 py-2 rounded-full" style="letter-spacing: 0.16px;">
            立即查看
          </span>
          <span class="text-amber-600 text-2xl">→</span>
        </div>
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Category Breakdown -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-medium text-gray-900 tracking-tight" style="letter-spacing: -0.4px;">支出分类</h2>
          <router-link to="/stats" class="text-blue-500 text-sm font-medium hover:underline" style="letter-spacing: 0.16px;">
            详情
          </router-link>
        </div>
        <div v-if="categoryBreakdown.length === 0" class="text-center py-12 text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-4">
          <div v-for="cat in categoryBreakdown" :key="cat.category_id" class="space-y-2">
            <div class="flex justify-between text-sm" style="letter-spacing: 0.16px;">
              <span class="text-gray-700">{{ cat.category_icon }} {{ cat.category_name }}</span>
              <span class="text-gray-500">{{ formatCurrency(cat.total_amount) }}</span>
            </div>
            <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-500 rounded-full"
                :style="{ width: `${cat.percentage}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Records -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-medium text-gray-900 tracking-tight" style="letter-spacing: -0.4px;">最近记录</h2>
          <router-link to="/records" class="text-blue-500 text-sm font-medium hover:underline" style="letter-spacing: 0.16px;">
            查看全部
          </router-link>
        </div>
        <div v-if="recentRecords.length === 0" class="text-center py-12">
          <p class="text-gray-500 mb-4 text-base" style="letter-spacing: 0.24px;">还没有记录</p>
          <router-link to="/upload" class="inline-block px-6 py-3 bg-gray-100 text-gray-900 rounded-full font-medium hover:opacity-85 transition-opacity text-sm">
            上传小票
          </router-link>
        </div>
        <div v-else class="space-y-4">
          <div
            v-for="record in recentRecords"
            :key="record.id"
            class="flex justify-between items-center p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <div class="flex items-center gap-4">
              <span class="text-2xl">{{ record.category_icon || '📦' }}</span>
              <div>
                <p class="text-base font-medium text-gray-900" style="letter-spacing: 0.24px;">{{ record.note || record.category_name }}</p>
                <p class="text-xs text-gray-500 mt-1" style="letter-spacing: 0.16px;">{{ formatDate(record.date) }}</p>
              </div>
            </div>
            <span :class="['text-xl font-medium', record.record_type === 'expense' ? 'text-red-500' : 'text-emerald-600']" style="letter-spacing: -0.32px;">
              {{ record.record_type === 'expense' ? '-' : '+' }}{{ formatCurrency(record.amount) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Record Modal -->
  <RecordModal :show="showRecordModal" @close="showRecordModal = false" />
</template>