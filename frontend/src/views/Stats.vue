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
    selectedYear.value--
    selectedMonth.value = 12
  } else {
    selectedMonth.value--
  }
  loadData()
}

function nextMonth() {
  if (selectedMonth.value === 12) {
    selectedYear.value++
    selectedMonth.value = 1
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

function getBarWidth(amount: number, max: number) {
  if (max === 0) return 0
  return (amount / max) * 100
}

const chartColors = ['#D4A843', '#3B82F6', '#22C55E', '#A855F7', '#F97316', '#EC4899']
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold" style="color: var(--text-primary);">📈 统计报表</h1>

    <!-- Month Selector -->
    <div
      class="rounded-2xl p-5 flex items-center justify-between"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
    >
      <button
        @click="prevMonth"
        class="p-2 rounded-xl transition"
        style="color: var(--accent-gold); background: var(--bg-hover);"
      >
        ◀
      </button>
      <span class="text-xl font-bold" style="color: var(--text-primary);">{{ currentMonthLabel }}</span>
      <button
        @click="nextMonth"
        class="p-2 rounded-xl transition"
        style="color: var(--accent-gold); background: var(--bg-hover);"
      >
        ▶
      </button>
    </div>

    <div v-if="loading" class="text-center py-12" style="color: var(--text-muted);">
      加载中...
    </div>

    <template v-else>
      <!-- Monthly Summary Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div
          class="rounded-2xl p-5"
          style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
        >
          <p class="text-sm mb-1" style="color: var(--text-muted);">本月收入</p>
          <p class="text-xl font-bold" style="color: var(--income-color);">{{ formatCurrency(monthlyStats?.total_income || 0) }}</p>
        </div>
        <div
          class="rounded-2xl p-5"
          style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
        >
          <p class="text-sm mb-1" style="color: var(--text-muted);">本月支出</p>
          <p class="text-xl font-bold" style="color: var(--expense-color);">{{ formatCurrency(monthlyStats?.total_expense || 0) }}</p>
        </div>
        <div
          class="rounded-2xl p-5"
          style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
        >
          <p class="text-sm mb-1" style="color: var(--text-muted);">本月结余</p>
          <p
            class="text-xl font-bold"
            :style="{ color: (monthlyStats?.balance || 0) >= 0 ? 'var(--income-color)' : 'var(--expense-color)' }"
          >
            {{ formatCurrency(monthlyStats?.balance || 0) }}
          </p>
        </div>
        <div
          class="rounded-2xl p-5"
          style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
        >
          <p class="text-sm mb-1" style="color: var(--text-muted);">记录数</p>
          <p class="text-xl font-bold text-gold">{{ monthlyStats?.record_count || 0 }}</p>
        </div>
      </div>

      <!-- Category Breakdown -->
      <div
        class="rounded-2xl p-6"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
      >
        <h2 class="text-lg font-semibold mb-5" style="color: var(--text-primary);">📊 支出分类</h2>
        <div v-if="categoryBreakdown.length === 0" class="text-center py-8" style="color: var(--text-muted);">
          暂无数据
        </div>
        <div v-else class="space-y-5">
          <div
            v-for="(cat, i) in categoryBreakdown"
            :key="cat.category_id"
            class="space-y-1.5"
          >
            <div class="flex justify-between items-center">
              <span class="flex items-center gap-2">
                <span class="text-xl">{{ cat.category_icon }}</span>
                <span class="font-medium" style="color: var(--text-primary);">{{ cat.category_name }}</span>
              </span>
              <span class="text-right">
                <span class="font-bold" style="color: var(--text-primary);">{{ formatCurrency(cat.total_amount) }}</span>
                <span class="text-sm ml-2" style="color: var(--text-muted);">{{ formatPercent(cat.percentage) }}</span>
              </span>
            </div>
            <div class="h-3 rounded-full overflow-hidden" style="background: var(--bg-hover);">
              <div
                class="h-full rounded-full transition-all"
                :style="{
                  width: `${getBarWidth(cat.total_amount, categoryBreakdown[0]?.total_amount || 1)}%`,
                  background: chartColors[i % chartColors.length]
                }"
              />
            </div>
            <p class="text-xs text-right" style="color: var(--text-muted);">{{ cat.record_count }} 笔</p>
          </div>
        </div>
      </div>

      <!-- Trend Chart -->
      <div
        class="rounded-2xl p-6"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
      >
        <h2 class="text-lg font-semibold mb-5" style="color: var(--text-primary);">📈 收支趋势（近6月）</h2>
        <div v-if="trendData.length === 0" class="text-center py-8" style="color: var(--text-muted);">
          暂无数据
        </div>
        <div v-else class="space-y-4">
          <div class="flex items-end justify-around h-48 gap-2">
            <div
              v-for="point in trendData"
              :key="`${point.year}-${point.month}`"
              class="flex-1 flex flex-col items-center gap-2"
            >
              <div
                class="w-full flex flex-col-reverse gap-1"
                style="height: 120px;"
              >
                <div
                  class="w-full rounded-t transition-all"
                  :style="{
                    height: `${getBarWidth(point.total_income, Math.max(...trendData.map(p => Math.max(p.total_income, p.total_expense))))}%`,
                    background: 'var(--income-color)',
                    opacity: 0.8
                  }"
                />
                <div
                  class="w-full rounded-t transition-all"
                  :style="{
                    height: `${getBarWidth(point.total_expense, Math.max(...trendData.map(p => Math.max(p.total_income, p.total_expense))))}%`,
                    background: 'var(--expense-color)',
                    opacity: 0.8
                  }"
                />
              </div>
              <span class="text-xs" style="color: var(--text-muted);">{{ point.month }}月</span>
            </div>
          </div>
          <div class="flex justify-center gap-6 text-sm">
            <span class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded" style="background: var(--income-color);"></span>
              <span style="color: var(--text-secondary);">收入</span>
            </span>
            <span class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded" style="background: var(--expense-color);"></span>
              <span style="color: var(--text-secondary);">支出</span>
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
