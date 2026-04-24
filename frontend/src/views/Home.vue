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

const router = useRouter()
const walletStore = useWalletStore()
const recordStore = useRecordStore()
const categoryStore = useCategoryStore()
const authStore = useAuthStore()
const aiRecordStore = useAIRecordStore()

const monthlyStats = ref<MonthlyStats | null>(null)
const categoryBreakdown = ref<CategoryBreakdown[]>([])
const recentRecords = computed(() => recordStore.records.slice(0, 5))

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
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-800">你好，{{ authStore.user?.username || '用户' }}</h1>
      <p class="text-gray-500">{{ currentMonth }}</p>
    </div>

    <!-- Balance Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gradient-to-r from-green-500 to-green-600 rounded-2xl p-6 text-white">
        <p class="text-green-100 mb-1">总资产</p>
        <p class="text-3xl font-bold">{{ formatCurrency(walletStore.totalBalance) }}</p>
      </div>
      <div class="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-6 text-white">
        <p class="text-blue-100 mb-1">本月收入</p>
        <p class="text-3xl font-bold">{{ formatCurrency(monthlyStats?.total_income || 0) }}</p>
      </div>
      <div class="bg-gradient-to-r from-red-500 to-red-600 rounded-2xl p-6 text-white">
        <p class="text-red-100 mb-1">本月支出</p>
        <p class="text-3xl font-bold">{{ formatCurrency(monthlyStats?.total_expense || 0) }}</p>
      </div>
    </div>

    <!-- Accounts Overview -->
    <div class="bg-white rounded-2xl shadow-sm p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-gray-800">💼 我的账户</h2>
        <router-link to="/wallets" class="text-indigo-600 text-sm hover:underline">管理</router-link>
      </div>
      <div v-if="walletStore.wallets.length === 0" class="text-center py-8 text-gray-500">
        <p class="mb-4">还没有账户</p>
        <router-link to="/wallets" class="text-indigo-600 hover:underline">创建账户</router-link>
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="wallet in walletStore.wallets"
          :key="wallet.id"
          class="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">
              {{ wallet.wallet_type === 'cash' ? '💵' : wallet.wallet_type === 'bank_card' ? '🏦' : wallet.wallet_type === 'e_wallet' ? '💳' : '💳' }}
            </span>
            <span class="font-medium">{{ wallet.name }}</span>
          </div>
          <span :class="['font-bold', wallet.balance >= 0 ? 'text-green-600' : 'text-red-600']">
            {{ formatCurrency(wallet.balance) }}
          </span>
        </div>
      </div>
    </div>

    <!-- AI Records Entry -->
    <div v-if="aiRecordStore.hasPendingRecords" class="bg-gradient-to-r from-yellow-50 to-orange-50 rounded-2xl shadow-sm border-2 border-yellow-200 overflow-hidden">
      <button
        @click="goToAIRecords"
        class="w-full p-5 flex items-center justify-between hover:from-yellow-100 hover:to-orange-100 transition-colors"
      >
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-yellow-400 rounded-2xl flex items-center justify-center relative">
            <span class="text-2xl">🤖</span>
            <!-- 动态小红点 -->
            <span
              v-if="aiRecordStore.showBadge"
              class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse border-2 border-white"
            />
          </div>
          <div class="text-left">
            <h3 class="font-semibold text-gray-800">有待确认的 AI 识别记录</h3>
            <p class="text-sm text-gray-500">
              共 {{ aiRecordStore.pendingCount }} 条记录待确认
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="bg-yellow-400 text-yellow-900 text-xs font-bold px-2.5 py-1 rounded-full">
            立即查看
          </span>
          <span class="text-yellow-500 text-xl">›</span>
        </div>
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Category Breakdown -->
      <div class="bg-white rounded-2xl shadow-sm p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold text-gray-800">📊 支出分类</h2>
          <router-link to="/stats" class="text-indigo-600 text-sm hover:underline">详情</router-link>
        </div>
        <div v-if="categoryBreakdown.length === 0" class="text-center py-8 text-gray-500">
          暂无数据
        </div>
        <div v-else class="space-y-3">
          <div v-for="cat in categoryBreakdown" :key="cat.category_id" class="space-y-1">
            <div class="flex justify-between text-sm">
              <span>{{ cat.category_icon }} {{ cat.category_name }}</span>
              <span class="text-gray-500">{{ formatCurrency(cat.total_amount) }}</span>
            </div>
            <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full bg-indigo-500 rounded-full"
                :style="{ width: `${cat.percentage}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Records -->
      <div class="bg-white rounded-2xl shadow-sm p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold text-gray-800">📝 最近记录</h2>
          <router-link to="/records" class="text-indigo-600 text-sm hover:underline">查看全部</router-link>
        </div>
        <div v-if="recentRecords.length === 0" class="text-center py-8 text-gray-500">
          <p class="mb-4">还没有记录</p>
          <router-link to="/upload" class="text-indigo-600 hover:underline">上传小票</router-link>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="record in recentRecords"
            :key="record.id"
            class="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
          >
            <div class="flex items-center gap-3">
              <span class="text-xl">{{ record.category_icon || '📦' }}</span>
              <div>
                <p class="font-medium">{{ record.note || record.category_name }}</p>
                <p class="text-xs text-gray-500">{{ formatDate(record.date) }}</p>
              </div>
            </div>
            <span :class="['font-bold', record.record_type === 'expense' ? 'text-red-500' : 'text-green-500']">
              {{ record.record_type === 'expense' ? '-' : '+' }}{{ formatCurrency(record.amount) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
