<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRecordStore } from '@/stores/record'
import { useWalletStore } from '@/stores/wallet'
import { useCategoryStore } from '@/stores/category'
import { useAuthStore } from '@/stores/auth'
import { aiApi } from '@/api'
import { RecordType } from '@/types'
import type { AIRecognizeResponse, AIRecognizeRecord } from '@/types'
import { onMounted, onUnmounted } from 'vue'

const router = useRouter()
const recordStore = useRecordStore()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()
const authStore = useAuthStore()

const fileInput = ref<HTMLInputElement>()
const preview = ref<string | null>(null)
const uploading = ref(false)
const aiResults = ref<AIRecognizeRecord[]>([])
const error = ref('')
const taskId = ref<string | null>(null)
const pollInterval = ref<ReturnType<typeof setInterval> | null>(null)
const recognitionProgress = ref('')
const autoSaving = ref(false)

const forms = ref<{
  wallet_id: number
  category_id: number | null
  amount: number
  record_type: 'expense' | 'income'
  note: string
  date: string
  saving: boolean
}[]>([])

const selectedWalletId = ref<number>(0)

function stopPolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

function toLocalDatetimeStr(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hour = pad(date.getHours())
  const min = pad(date.getMinutes())
  return `${year}-${month}-${day}T${hour}:${min}`
}

function todayDateStr() {
  return toLocalDatetimeStr(new Date()).slice(0, 10)
}

function parseAiDate(dateStr: string | null | undefined): string {
  if (!dateStr) return toLocalDatetimeStr(new Date())
  const trimmed = dateStr.trim()
  if (/^\d{4}-\d{2}-\d{2}/.test(trimmed)) return trimmed.slice(0, 16)
  if (/^\d{1,2}:\d{2}/.test(trimmed)) return `${todayDateStr()} ${trimmed.trim()}`
  return toLocalDatetimeStr(new Date())
}

async function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (preview.value) URL.revokeObjectURL(preview.value)
  preview.value = URL.createObjectURL(file)

  stopPolling()
  aiResults.value = []
  forms.value = []
  error.value = ''
  taskId.value = null

  uploading.value = true
  recognitionProgress.value = '正在上传图片...'
  try {
    const res = await aiApi.recognizeAsync(file)
    const data = res.data
    taskId.value = data.task_id

    recognitionProgress.value = 'AI 正在识别中（首次识别可能需要 20-60 秒）...'
    pollInterval.value = setInterval(async () => {
      try {
        const pollRes = await aiApi.getRecognizeResult(taskId.value!)
        const pollData = pollRes.data

        if (pollData.status === 'pending') {
          recognitionProgress.value = 'AI 正在识别中，请稍候...'
        } else if (pollData.status === 'done') {
          stopPolling()
          const result = pollData.result!
          const records: AIRecognizeRecord[] = result.records || []

          if (records.length === 0) {
            aiResults.value = [{
              amount: result.amount || 0,
              merchant_name: result.merchant_name || '',
              date: result.date || '',
              category_guess: result.category_guess || '',
              category_id: result.category_id || null,
              confidence: result.confidence || 0,
              record_type: 'expense',
            }]
          } else {
            aiResults.value = records
          }

          forms.value = aiResults.value.map((r: AIRecognizeRecord) => {
            const rt = (r.record_type === 'income' ? 'income' : 'expense') as 'expense' | 'income'
            return {
              wallet_id: selectedWalletId.value || walletStore.wallets[0]?.id || 0,
              category_id: r.category_id || null,
              amount: r.amount || 0,
              record_type: rt,
              note: r.merchant_name || '',
              date: parseAiDate(r.date),
              saving: false,
            }
          })
          recognitionProgress.value = ''
          uploading.value = false

          if (aiResults.value.length > 0 && aiResults.value.every(r => (r.confidence || 0) >= 0.85)) {
            autoSaving.value = true
            await handleSaveAll()
            return
          }
        } else {
          stopPolling()
          error.value = '识别失败，请重试'
          uploading.value = false
          if (fileInput.value) fileInput.value.value = ''
        }
      } catch {
        // Poll error — keep polling
      }
    }, 3000)
  } catch (e: any) {
    stopPolling()
    error.value = e.response?.data?.detail || '上传失败，请重试'
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
    preview.value = null
  }
}

async function handleSaveAll() {
  if (forms.value.length === 0) return
  let savedCount = 0
  let failedCount = 0
  for (let i = 0; i < forms.value.length; i++) {
    const form = forms.value[i]
    if (form.saving) continue
    form.saving = true
    try {
      await recordStore.createRecord({
        wallet_id: form.wallet_id,
        category_id: form.category_id,
        amount: form.amount,
        record_type: form.record_type === 'income' ? RecordType.INCOME : RecordType.EXPENSE,
        note: form.note,
        date: new Date(form.date).toISOString(),
      })
      savedCount++
    } catch (e: any) {
      failedCount++
      form.saving = false
      error.value = `保存第 ${i + 1} 条记录失败：${e.response?.data?.detail || e.message || '未知错误'}`
    }
  }
  if (failedCount === 0) {
    router.push('/records')
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

onMounted(async () => {
  await Promise.all([
    walletStore.fetchWallets(),
    categoryStore.fetchCategories(),
  ])
  if (walletStore.wallets.length > 0) {
    const userDefaultWalletId = authStore.user?.default_wallet_id
    if (userDefaultWalletId && walletStore.wallets.some(w => w.id === userDefaultWalletId)) {
      selectedWalletId.value = userDefaultWalletId
    } else {
      selectedWalletId.value = walletStore.wallets[0].id
    }
  }
})

onUnmounted(() => { stopPolling() })
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold" style="color: var(--text-primary);">🤖 AI 识别记账</h1>

    <!-- Wallet selector -->
    <div
      v-if="walletStore.wallets.length > 0"
      class="rounded-xl p-4"
      style="background: var(--bg-card); border: 1px solid var(--border-color);"
    >
      <label class="block text-sm font-medium mb-2" style="color: var(--text-secondary);">默认账户（可单独修改）</label>
      <select v-model="selectedWalletId" class="input-gold">
        <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
      </select>
    </div>

    <!-- Upload Area -->
    <div
      @click="triggerFileInput"
      class="rounded-2xl p-12 text-center cursor-pointer transition"
      style="border: 2px dashed var(--border-strong);"
      :style="{ borderColor: 'var(--accent-gold)' }"
    >
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        @change="handleFileSelect"
        class="hidden"
      />
      <div v-if="!preview" class="space-y-4">
        <div class="text-6xl">📷</div>
        <div>
          <p class="text-lg font-medium" style="color: var(--text-primary);">点击上传小票图片</p>
          <p class="text-sm mt-1" style="color: var(--text-muted);">支持 JPG、PNG、WebP 格式</p>
        </div>
      </div>
      <img v-else :src="preview" class="max-h-72 mx-auto rounded-xl" alt="Preview" />
    </div>

    <!-- Loading / Polling -->
    <div v-if="uploading" class="text-center py-8">
      <div class="text-4xl mb-4 animate-pulse">⏳</div>
      <p style="color: var(--text-muted);">{{ recognitionProgress || 'AI 正在识别中...' }}</p>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="p-4 rounded-xl text-sm"
      style="background: rgba(239,68,68,0.1); color: var(--expense-color); border: 1px solid rgba(239,68,68,0.2);"
    >
      {{ error }}
    </div>

    <!-- AI Results -->
    <div v-if="aiResults.length > 0 && !uploading" class="space-y-4">
      <div class="flex items-center gap-2" style="color: var(--income-color);">
        <span class="text-xl">✅</span>
        <span class="font-medium">识别成功</span>
        <span class="text-sm" style="color: var(--text-muted); margin-left: 8px;">
          共 {{ aiResults.length }} 条记录
        </span>
      </div>

      <!-- Per-record editing cards -->
      <div
        v-for="(result, index) in aiResults"
        :key="index"
        class="rounded-2xl p-6 space-y-4"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
      >
        <div class="flex items-center justify-between">
          <h3 class="font-semibold" style="color: var(--text-primary);">记录 {{ index + 1 }}</h3>
          <div class="flex items-center gap-2">
            <select
              v-model="forms[index].record_type"
              class="text-xs px-2 py-0.5 rounded-full border"
              :style="
                forms[index].record_type === 'income'
                  ? 'background: rgba(34,197,94,0.1); color: var(--income-color); border-color: rgba(34,197,94,0.3);'
                  : 'background: rgba(239,68,68,0.1); color: var(--expense-color); border-color: rgba(239,68,68,0.3);'
              "
            >
              <option value="expense">💸 支出</option>
              <option value="income">💰 退款/收入</option>
            </select>
            <span
              class="text-xs px-2 py-0.5 rounded-full"
              :style="
                (result.confidence || 0) >= 0.85
                  ? 'background: rgba(34,197,94,0.1); color: var(--income-color);'
                  : 'background: var(--accent-gold-light); color: var(--accent-gold);'
              "
            >
              置信度: {{ ((result.confidence || 0) * 100).toFixed(0) }}%
            </span>
          </div>
        </div>

        <!-- AI recognized summary -->
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div
            class="p-3 rounded-lg"
            :style="forms[index].record_type === 'income' ? 'background: rgba(34,197,94,0.08);' : 'background: var(--bg-hover);'"
          >
            <p class="text-xs" style="color: var(--text-muted);">
              {{ forms[index].record_type === 'income' ? '退款/收入' : '消费金额' }}
            </p>
            <p
              class="font-bold text-lg"
              :style="{ color: forms[index].record_type === 'income' ? 'var(--income-color)' : 'var(--expense-color)' }"
            >
              ¥{{ result.amount?.toFixed(2) || '-' }}
            </p>
          </div>
          <div class="p-3 rounded-lg" style="background: var(--bg-hover);">
            <p class="text-xs" style="color: var(--text-muted);">识别商户</p>
            <p class="font-medium" style="color: var(--text-primary);">{{ result.merchant_name || '-' }}</p>
          </div>
          <div class="p-3 rounded-lg" style="background: var(--bg-hover);">
            <p class="text-xs" style="color: var(--text-muted);">识别日期</p>
            <p class="font-medium" style="color: var(--text-primary);">{{ result.date || '-' }}</p>
          </div>
          <div class="p-3 rounded-lg" style="background: var(--bg-hover);">
            <p class="text-xs" style="color: var(--text-muted);">建议分类</p>
            <p class="font-medium" style="color: var(--text-primary);">{{ result.category_guess || '-' }}</p>
          </div>
        </div>

        <hr style="border-color: var(--border-color);" />

        <!-- Editable form -->
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary);">金额 *</label>
              <input
                v-model.number="forms[index].amount"
                type="number"
                step="0.01"
                class="input-gold"
                required
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary);">账户 *</label>
              <select v-model="forms[index].wallet_id" class="input-gold" required>
                <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">
                  {{ w.name }}
                </option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary);">分类</label>
            <select v-model="forms[index].category_id" class="input-gold">
              <option :value="null">未分类</option>
              <option v-for="c in categoryStore.categories" :key="c.id" :value="c.id">
                {{ c.icon }} {{ c.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary);">备注</label>
            <input v-model="forms[index].note" type="text" class="input-gold" />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary);">日期</label>
            <input v-model="forms[index].date" type="datetime-local" class="input-gold" />
          </div>
        </div>
      </div>

      <!-- Save All Button -->
      <button @click="handleSaveAll" class="btn-gold w-full py-3">
        保存全部 {{ aiResults.length }} 条记录
      </button>
    </div>

    <!-- No results yet -->
    <div
      v-if="!aiResults.length && !uploading"
      class="text-center py-8"
      style="color: var(--text-muted);"
    >
      <p>上传小票图片，AI 自动识别金额、商户等信息</p>
      <p class="text-sm mt-2">支持同时识别多条消费记录</p>
    </div>
  </div>
</template>
