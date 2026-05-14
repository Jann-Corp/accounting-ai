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
      <h1 class="text-2xl font-bold" style="color: var(--text-primary);">
        你好，{{ authStore.user?.username || '用户' }} 👋
      </h1>
      <p style="color: var(--text-muted);">{{ currentMonth }}</p>
    </div>

    <!-- Balance Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Total Balance -->
      <div class="rounded-2xl p-6 text-white relative overflow-hidden" style="background: linear-gradient(135deg, #B8922E, #D4A843, #F5D98B);">
        <div class="absolute top-0 right-0 w-32 h-32 opacity-10 text-8xl">💰</div>
        <p class="text-sm mb-1" style="color: rgba(255,255,255,0.8);">总资产</p>
        <p class="text-3xl font-bold text-amount">{{ formatCurrency(walletStore.totalBalance) }}</p>
      </div>
      <!-- Income -->
      <div class="rounded-2xl p-6 text-white relative overflow-hidden" style="background: linear-gradient(135deg, #15803D, #22C55E, #86EFAC);">
        <div class="absolute top-0 right-0 w-32 h-32 opacity-10 text-8xl">📈</div>
        <p class="text-sm mb-1" style="color: rgba(255,255,255,0.8);">本月收入</p>
        <p class="text-3xl font-bold text-amount">{{ formatCurrency(monthlyStats?.total_income || 0) }}</p>
      </div>
      <!-- Expense -->
      <div class="rounded-2xl p-6 text-white relative overflow-hidden" style="background: linear-gradient(135deg, #B91C1C, #EF4444, #FCA5A5);">
        <div class="absolute top-0 right-0 w-32 h-32 opacity-10 text-8xl">📉</div>
        <p class="text-sm mb-1" style="color: rgba(255,255,255,0.8);">本月支出</p>
        <p class="text-3xl font-bold text-amount">{{ formatCurrency(monthlyStats?.total_expense || 0) }}</p>
      </div>
    </div>

    <!-- AI Records Entry -->
    <div
      v-if="aiRecordStore.hasPendingRecords"
      class="rounded-2xl p-5 cursor-pointer border transition-all"
      style="background: var(--bg-card); border-color: var(--accent-gold); box-shadow: var(--shadow-gold);"
      @click="goToAIRecords"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div
            class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl relative"
            style="background: var(--accent-gold-light);"
          >
            🤖
            <span
              v-if="aiRecordStore.showBadge"
              class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse border-2 border-white"
            />
          </div>
          <div class="text-left">
            <h3 class="font-semibold" style="color: var(--text-primary);">有待确认的 AI 识别记录</h3>
            <p class="text-sm" style="color: var(--text-muted);">
              共 {{ aiRecordStore.pendingCount }} 条记录待确认
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="badge-gold">立即查看</span>
          <span style="color: var(--accent-gold);" class="text-xl">›</span>
        </div>
      </div>
    </div>

    <!-- Accounts Overview -->
    <div class="rounded-2xl p-6" style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold" style="color: var(--text-primary);">💼 我的账户</h2>
        <router-link to="/wallets" class="text-sm font-medium" style="color: var(--accent-gold);">管理 ›</router-link>
      </div>
      <div v-if="walletStore.wallets.length === 0" class="text-center py-8" style="color: var(--text-muted);">
        <p class="mb-4">还没有账户</p>
        <router-link to="/wallets" class="font-medium" style="color: var(--accent-gold);">创建账户</router-link>
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="wallet in walletStore.wallets"
          :key="wallet.id"
          class="flex justify-between items-center p-3 rounded-xl transition"
          style="background: var(--bg-hover);"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">
              {{ wallet.wallet_type === 'cash' ? '💵' : wallet.wallet_type === 'bank_card' ? '🏦' : '💳' }}
            </span>
            <span class="font-medium" style="color: var(--text-primary);">{{ wallet.name }}</span>
          </div>
          <span
            class="font-bold text-amount"
            :style="{ color: wallet.balance >= 0 ? 'var(--income-color)' : 'var(--expense-color)' }"
          >
            {{ formatCurrency(wallet.balance) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Bottom Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Category Breakdown -->
      <div class="rounded-2xl p-6" style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold" style="color: var(--text-primary);">📊 支出分类</h2>
          <router-link to="/stats" class="text-sm font-medium" style="color: var(--accent-gold);">详情 ›</router-link>
        </div>
        <div v-if="categoryBreakdown.length === 0" class="text-center py-8" style="color: var(--text-muted);">
          暂无数据
        </div>
        <div v-else class="space-y-3">
          <div v-for="(cat, i) in categoryBreakdown" :key="cat.category_id" class="space-y-1">
            <div class="flex justify-between text-sm">
              <span style="color: var(--text-primary);">
                <span class="mr-1">{{ cat.category_icon }}</span>
                {{ cat.category_name }}
              </span>
              <span style="color: var(--text-muted);">{{ formatCurrency(cat.total_amount) }}</span>
            </div>
            <div class="h-2 rounded-full overflow-hidden" style="background: var(--bg-hover);">
              <div
                class="h-full rounded-full transition-all"
                :class="['chart-bar-' + i]"
                :style="{
                  width: `${cat.percentage}%`,
                  background: ['#D4A843', '#3B82F6', '#22C55E', '#A855F7', '#F97316', '#EC4899'][i % 6]
                }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Records -->
      <div class="rounded-2xl p-6" style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold" style="color: var(--text-primary);">📝 最近记录</h2>
          <router-link to="/records" class="text-sm font-medium" style="color: var(--accent-gold);">查看全部 ›</router-link>
        </div>
        <div v-if="recentRecords.length === 0" class="text-center py-8" style="color: var(--text-muted);">
          <p class="mb-4">还没有记录</p>
          <router-link to="/upload" class="font-medium" style="color: var(--accent-gold);">上传小票</router-link>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="record in recentRecords"
            :key="record.id"
            class="flex justify-between items-center p-3 rounded-xl transition"
            style="background: var(--bg-hover);"
          >
            <div class="flex items-center gap-3">
              <span class="text-xl">{{ record.category_icon || '📦' }}</span>
              <div>
                <p class="font-medium" style="color: var(--text-primary);">{{ record.note || record.category_name }}</p>
                <p class="text-xs" style="color: var(--text-muted);">{{ formatDate(record.date) }}</p>
              </div>
            </div>
            <span
              class="font-bold text-amount"
              :style="{ color: record.record_type === 'expense' ? 'var(--expense-color)' : 'var(--income-color)' }"
            >
              {{ record.record_type === 'expense' ? '-' : '+' }}{{ formatCurrency(record.amount) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
