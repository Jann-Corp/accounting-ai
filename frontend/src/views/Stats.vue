<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { statsApi } from '@/api'
import type { MonthlyStats, CategoryBreakdown, TrendPoint } from '@/types'

const currentDate = new Date()
const selectedYear = ref(currentDate.getFullYear())
const selectedMonth = ref(currentDate.getMonth() + 1)

const monthlyStats = ref<MonthlyStats | null>(null)
const categoryBreakdown = ref<CategoryBreakdown[]>([])
const trendData = ref<TrendPoint[]>([])

const loading = ref(false)

const currentMonthLabel = computed(() => 
  `${selectedYear.value}年${selectedMonth.value}月`
)

async function loadData() {
  loading.value = true
  try {
    const [statsRes, breakdownRes, trendRes] = await Promise.all([
      statsApi.monthly(selectedYear.value, selectedMonth.value),
      statsApi.categoryBreakdown(selectedYear.value, selectedMonth.value),
      statsApi.trend(6),
    ])
    monthlyStats.value = statsRes.data
    categoryBreakdown.value = breakdownRes.data.breakdown
    trendData.value = trendRes.data.trend
  } catch (e) {
    console.error('Failed to load stats', e)
  } finally {
    loading.value = false
  }
}

function prevMonth() {
  if (selectedMonth.value === 1) {
    selectedMonth.value = 12
    selectedYear.value--
  } else {
    selectedMonth.value--
  }
  loadData()
}

function nextMonth() {
  if (selectedMonth.value === 12) {
    selectedMonth.value = 1
    selectedYear.value++
  } else {
    selectedMonth.value++
  }
  loadData()
}

onMounted(() => {
  loadData()
})

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(amount)
}

function formatPercent(value: number) {
  return `${value.toFixed(1)}%`
}

// Simple bar chart component inline
function getBarWidth(amount: number, max: number) {
  if (max === 0) return 0
  return (amount / max) * 100
}
</script>

<template>
  <div class="space-y-8">
    <h1 class="text-5xl font-semibold text-gray-900 tracking-tight">统计报表</h1>

    <!-- Month Selector -->
    <div class="border border-gray-100 bg-white rounded-2xl p-6">
      <div class="flex items-center justify-between">
        <button @click="prevMonth" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span class="text-xl font-semibold text-gray-900">{{ currentMonthLabel }}</span>
        <button @click="nextMonth" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400">加载中...</div>

    <template v-else>
      <!-- Monthly Summary -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="border border-gray-100 bg-white rounded-2xl p-6">
          <p class="text-gray-500 mb-2 text-sm">本月收入</p>
          <p class="text-2xl font-semibold text-emerald-600">{{ formatCurrency(monthlyStats?.total_income || 0) }}</p>
        </div>
        <div class="border border-gray-100 bg-white rounded-2xl p-6">
          <p class="text-gray-500 mb-2 text-sm">本月支出</p>
          <p class="text-2xl font-semibold text-red-500">{{ formatCurrency(monthlyStats?.total_expense || 0) }}</p>
        </div>
        <div class="border border-gray-100 bg-white rounded-2xl p-6">
          <p class="text-gray-500 mb-2 text-sm">本月结余</p>
          <p :class="['text-2xl font-semibold', (monthlyStats?.balance || 0) >= 0 ? 'text-emerald-600' : 'text-red-500']">
            {{ formatCurrency(monthlyStats?.balance || 0) }}
          </p>
        </div>
        <div class="border border-gray-100 bg-white rounded-2xl p-6">
          <p class="text-gray-500 mb-2 text-sm">记录数</p>
          <p class="text-2xl font-semibold text-gray-900">{{ monthlyStats?.record_count || 0 }}</p>
        </div>
      </div>

      <!-- Category Breakdown -->
      <div class="border border-gray-100 bg-white rounded-2xl p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-6 tracking-tight">支出分类</h2>
        <div v-if="categoryBreakdown.length === 0" class="text-center py-12 text-gray-400">
          暂无数据
        </div>
        <div v-else class="space-y-5">
          <div v-for="cat in categoryBreakdown" :key="cat.category_id" class="space-y-2">
            <div class="flex justify-between items-center">
              <span class="flex items-center gap-3">
                <span class="text-xl">{{ cat.category_icon }}</span>
                <span class="font-medium text-gray-900">{{ cat.category_name }}</span>
              </span>
              <span class="text-right">
                <span class="font-semibold text-gray-900">{{ formatCurrency(cat.total_amount) }}</span>
                <span class="text-gray-400 text-sm ml-2">{{ formatPercent(cat.percentage) }}</span>
              </span>
            </div>
            <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full bg-gray-900 rounded-full transition-all"
                :style="{ width: `${getBarWidth(cat.total_amount, categoryBreakdown[0]?.total_amount || 1)}%` }"
              />
            </div>
            <p class="text-xs text-gray-400 text-right">{{ cat.record_count }} 笔</p>
          </div>
        </div>
      </div>

      <!-- Trend Chart -->
      <div class="border border-gray-100 bg-white rounded-2xl p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-6 tracking-tight">收支趋势（近6月）</h2>
        <div v-if="trendData.length === 0" class="text-center py-12 text-gray-400">
          暂无数据
        </div>
        <div v-else class="space-y-5">
          <div class="flex items-end justify-around h-56 gap-2">
            <div v-for="point in trendData" :key="`${point.year}-${point.month}`" class="flex-1 flex flex-col items-center gap-2">
              <div class="w-full flex flex-col-reverse gap-1" style="height: 120px">
                <div
                  class="w-full bg-emerald-400 rounded-t transition-all"
                  :style="{ height: `${getBarWidth(point.total_income, Math.max(...trendData.map(p => Math.max(p.total_income, p.total_expense))))}%` }"
                />
                <div
                  class="w-full bg-red-400 rounded-t transition-all"
                  :style="{ height: `${getBarWidth(point.total_expense, Math.max(...trendData.map(p => Math.max(p.total_income, p.total_expense))))}%` }"
                />
              </div>
              <span class="text-xs text-gray-500">{{ point.month }}月</span>
            </div>
          </div>
          <div class="flex justify-center gap-6 text-sm text-gray-600">
            <span class="flex items-center gap-2"><span class="w-3 h-3 bg-emerald-400 rounded"></span> 收入</span>
            <span class="flex items-center gap-2"><span class="w-3 h-3 bg-red-400 rounded"></span> 支出</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
