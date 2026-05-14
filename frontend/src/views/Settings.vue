<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useWalletStore } from '@/stores/wallet'
import { useThemeStore } from '@/stores/theme'
import { exchangeRateApi, type ExchangeRate } from '@/api'

const authStore = useAuthStore()
const walletStore = useWalletStore()
const themeStore = useThemeStore()

const saving = ref(false)
const error = ref('')
const success = ref('')
const selectedWalletId = ref<number | null>(null)

// Exchange rates
const rates = ref<ExchangeRate[]>([])
const loadingRates = ref(false)
const newCurrency = ref('')
const newRate = ref('')
const addingRate = ref(false)
const rateError = ref('')
const rateSuccess = ref('')

// Common currencies
const commonCurrencies = ['USD', 'EUR', 'GBP', 'JPY', 'KRW', 'HKD', 'TWD', 'SGD', 'AUD', 'CAD']

async function handleSave() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    await authStore.updateDefaultWallet(selectedWalletId.value)
    success.value = '✅ 设置已保存'
  } catch (e: any) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function loadRates() {
  loadingRates.value = true
  try {
    const res = await exchangeRateApi.list()
    rates.value = res.data
  } catch (e: any) {
    rateError.value = '加载汇率失败'
  } finally {
    loadingRates.value = false
  }
}

async function addRate() {
  if (!newCurrency.value.trim() || !newRate.value) {
    rateError.value = '请填写货币代码和汇率'
    return
  }
  const currency = newCurrency.value.trim().toUpperCase()
  const rate = parseFloat(newRate.value)
  if (isNaN(rate) || rate <= 0) {
    rateError.value = '汇率必须为正数'
    return
  }
  addingRate.value = true
  rateError.value = ''
  rateSuccess.value = ''
  try {
    await exchangeRateApi.upsert(currency, rate)
    rateSuccess.value = `✅ 已添加/更新 ${currency} 汇率`
    newCurrency.value = ''
    newRate.value = ''
    await loadRates()
  } catch (e: any) {
    rateError.value = e.message || '添加失败'
  } finally {
    addingRate.value = false
  }
}

async function removeRate(currency: string) {
  try {
    await exchangeRateApi.remove(currency)
    await loadRates()
  } catch (e: any) {
    rateError.value = e.message || '删除失败'
  }
}

onMounted(async () => {
  await walletStore.fetchWallets()
  if (authStore.user?.default_wallet_id) {
    selectedWalletId.value = authStore.user.default_wallet_id
  }
  await loadRates()
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold" style="color: var(--text-primary);">⚙️ 设置</h1>

    <!-- Default Wallet -->
    <div
      class="rounded-2xl p-6"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
    >
      <h2 class="text-lg font-semibold mb-1" style="color: var(--text-primary);">📦 默认账户</h2>
      <p class="text-sm mb-5" style="color: var(--text-muted);">
        AI 识别记账时默认使用的账户，可在上传页面单独修改。
      </p>
      <div class="space-y-4">
        <select v-model="selectedWalletId" class="input-gold">
          <option :value="null">不设置（每次手动选择）</option>
          <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">
            {{ w.name }}
          </option>
        </select>

        <div v-if="success" class="p-3 rounded-xl text-sm" style="background: rgba(34,197,94,0.1); color: var(--income-color);">
          {{ success }}
        </div>
        <div v-if="error" class="p-3 rounded-xl text-sm" style="background: rgba(239,68,68,0.1); color: var(--expense-color);">
          {{ error }}
        </div>

        <button
          @click="handleSave"
          :disabled="saving"
          class="btn-gold w-full"
        >
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>
    </div>

    <!-- Exchange Rates -->
    <div
      class="rounded-2xl p-6"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
    >
      <h2 class="text-lg font-semibold mb-1" style="color: var(--text-primary);">💱 货币汇率</h2>
      <p class="text-sm mb-5" style="color: var(--text-muted);">
        设置外币兑换人民币的汇率，用于多币种账户记账。汇率 = 1 外币 = × 元人民币
      </p>

      <!-- Add new rate -->
      <div class="flex gap-3 mb-6">
        <input
          v-model="newCurrency"
          placeholder="USD"
          maxlength="10"
          class="input-gold flex-1 text-center uppercase"
          @keyup.enter="addRate"
        />
        <input
          v-model="newRate"
          type="number"
          step="0.0001"
          min="0.0001"
          placeholder="7.2000"
          class="input-gold flex-1 text-center"
          @keyup.enter="addRate"
        />
        <button
          @click="addRate"
          :disabled="addingRate"
          class="btn-gold px-6"
        >
          {{ addingRate ? '...' : '+ 添加' }}
        </button>
      </div>

      <!-- Quick add common -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button
          v-for="c in commonCurrencies.filter(x => !rates.find(r => r.currency === x))"
          :key="c"
          @click="newCurrency = c; newRate = ''"
          class="px-3 py-1 rounded-lg text-xs transition"
          style="background: var(--bg-secondary); color: var(--text-muted); border: 1px solid var(--border-color);"
          :style="{ cursor: 'pointer' }"
        >
          {{ c }}
        </button>
      </div>

      <!-- Error / Success -->
      <div v-if="rateError" class="p-3 rounded-xl text-sm mb-4" style="background: rgba(239,68,68,0.1); color: var(--expense-color);">
        {{ rateError }}
      </div>
      <div v-if="rateSuccess" class="p-3 rounded-xl text-sm mb-4" style="background: rgba(34,197,94,0.1); color: var(--income-color);">
        {{ rateSuccess }}
      </div>

      <!-- Rates list -->
      <div v-if="loadingRates" class="text-center py-4" style="color: var(--text-muted);">
        加载中...
      </div>
      <div v-else-if="rates.length === 0" class="text-center py-4" style="color: var(--text-muted);">
        暂无自定义汇率，使用系统默认汇率
      </div>
      <div v-else class="space-y-2">
        <div
          v-for="r in rates"
          :key="r.id"
          class="flex items-center justify-between p-3 rounded-xl"
          style="background: var(--bg-secondary);"
        >
          <div class="flex items-center gap-3">
            <span class="font-mono font-bold text-lg" style="color: var(--accent-gold);">{{ r.currency }}</span>
            <span style="color: var(--text-muted);">=</span>
            <span class="font-mono font-semibold" style="color: var(--text-primary);">{{ r.rate.toFixed(4) }}</span>
            <span style="color: var(--text-muted);">CNY</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs" style="color: var(--text-muted);">{{ new Date(r.updated_at).toLocaleDateString('zh-CN') }}</span>
            <button
              @click="removeRate(r.currency)"
              class="px-3 py-1 rounded-lg text-xs transition"
              style="background: rgba(239,68,68,0.1); color: var(--expense-color);"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Theme Setting -->
    <div
      class="rounded-2xl p-6"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
    >
      <h2 class="text-lg font-semibold mb-1" style="color: var(--text-primary);">🎨 外观</h2>
      <p class="text-sm mb-5" style="color: var(--text-muted);">
        选择你喜欢的主题风格
      </p>
      <div class="grid grid-cols-2 gap-4">
        <button
          @click="themeStore.isDark = false"
          class="rounded-xl p-4 text-center transition border-2"
          :style="
            !themeStore.isDark
              ? 'border-color: var(--accent-gold); background: var(--accent-gold-light);'
              : 'border-color: var(--border-color);'
          "
        >
          <div class="text-4xl mb-2">☀️</div>
          <div class="font-medium text-sm" style="color: var(--text-primary);">浅色模式</div>
          <div class="text-xs mt-1" style="color: var(--text-muted);">明亮清爽</div>
        </button>
        <button
          @click="themeStore.isDark = true"
          class="rounded-xl p-4 text-center transition border-2"
          :style="
            themeStore.isDark
              ? 'border-color: var(--accent-gold); background: var(--accent-gold-light);'
              : 'border-color: var(--border-color);'
          "
        >
          <div class="text-4xl mb-2">🌙</div>
          <div class="font-medium text-sm" style="color: var(--text-primary);">深色模式</div>
          <div class="text-xs mt-1" style="color: var(--text-muted);">暗金典雅</div>
        </button>
      </div>
    </div>

    <!-- User Info -->
    <div
      class="rounded-2xl p-6"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
    >
      <h2 class="text-lg font-semibold mb-4" style="color: var(--text-primary);">👤 账户信息</h2>
      <div class="space-y-0">
        <div
          v-for="(item, i) in [
            { label: '用户名', value: authStore.user?.username },
            { label: '邮箱', value: authStore.user?.email },
            { label: '注册时间', value: new Date(authStore.user?.created_at || '').toLocaleDateString('zh-CN') },
          ]"
          :key="i"
          class="flex justify-between py-3"
          :style="i < 2 ? 'border-bottom: 1px solid var(--border-color);' : ''"
        >
          <span style="color: var(--text-muted);">{{ item.label }}</span>
          <span class="font-medium" style="color: var(--text-primary);">{{ item.value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
