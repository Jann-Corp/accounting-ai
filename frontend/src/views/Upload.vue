<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRecordStore } from '@/stores/record'
import { useWalletStore } from '@/stores/wallet'
import { useCategoryStore } from '@/stores/category'
import { aiApi } from '@/api'
import { RecordType } from '@/types'
import type { AIRecognizeResponse, AIRecognizeRecord } from '@/types'

const router = useRouter()
const recordStore = useRecordStore()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()

const fileInput = ref<HTMLInputElement>()
const preview = ref<string | null>(null)
const uploading = ref(false)
const aiResults = ref<AIRecognizeRecord[]>([])
const error = ref('')
const taskId = ref<string | null>(null)
const pollInterval = ref<ReturnType<typeof setInterval> | null>(null)
const recognitionProgress = ref('')

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

async function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // Preview
  if (preview.value) URL.revokeObjectURL(preview.value)
  preview.value = URL.createObjectURL(file)

  // Reset previous results
  stopPolling()
  aiResults.value = []
  forms.value = []
  error.value = ''
  taskId.value = null

  // Upload and start async recognition
  uploading.value = true
  recognitionProgress.value = '正在上传图片...'
  try {
    const res = await aiApi.recognizeAsync(file)
    const data = res.data
    taskId.value = data.task_id

    // Start polling
    recognitionProgress.value = 'AI 正在识别中（首次识别可能需要 20-60 秒）...'
    pollInterval.value = setInterval(async () => {
      try {
        const pollRes = await aiApi.getRecognizeResult(taskId.value!)
        const pollData = pollRes.data

        if (pollData.status === 'pending') {
          // Still working — just update progress text
          recognitionProgress.value = 'AI 正在识别中，请稍候...'
        } else if (pollData.status === 'done') {
          stopPolling()
          const result = pollData.result
          const records: AIRecognizeRecord[] = result.records || []

          if (records.length === 0) {
            // Fallback to top-level fields
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

          // Initialize forms
          forms.value = aiResults.value.map((r: AIRecognizeRecord) => ({
            wallet_id: selectedWalletId.value || walletStore.wallets[0]?.id || 0,
            category_id: r.category_id || null,
            amount: r.amount || 0,
            record_type: (r.record_type === 'income' ? 'income' : 'expense') as 'expense' | 'income',
            note: r.merchant_name || '',
            date: new Date().toISOString().slice(0, 16),
            saving: false,
          }))
          recognitionProgress.value = ''
          uploading.value = false
        } else {
          stopPolling()
          error.value = '识别失败，请重试'
          uploading.value = false
          // Allow re-upload
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
    // Allow re-upload
    if (fileInput.value) fileInput.value.value = ''
    preview.value = null
  }
}

async function handleSaveAll() {
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
    } finally {
      form.saving = false
    }
  }
  router.push('/records')
}

function triggerFileInput() {
  fileInput.value?.click()
}

// Load wallets and categories on mount
import { onMounted } from 'vue'
onMounted(async () => {
  await Promise.all([
    walletStore.fetchWallets(),
    categoryStore.fetchCategories(),
  ])
  if (walletStore.wallets.length > 0) {
    selectedWalletId.value = walletStore.wallets[0].id
  }
})

// Cleanup polling on unmount
import { onUnmounted } from 'vue'
onUnmounted(() => { stopPolling() })
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-800">🤖 AI 识别记账</h1>

    <!-- Wallet selector (global for all records) -->
    <div v-if="walletStore.wallets.length > 0" class="bg-white rounded-2xl shadow-sm p-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">默认账户（可单独修改）</label>
      <select v-model="selectedWalletId" class="w-full border rounded-lg px-3 py-2">
        <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
      </select>
    </div>

    <!-- Upload Area -->
    <div
      @click="triggerFileInput"
      class="border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center cursor-pointer hover:border-indigo-400 transition"
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
          <p class="text-lg font-medium text-gray-700">点击上传小票图片</p>
          <p class="text-sm text-gray-500 mt-1">支持 JPG、PNG、WebP 格式</p>
        </div>
      </div>
      <img v-else :src="preview" class="max-h-72 mx-auto rounded-lg" alt="Preview" />
    </div>

    <!-- Loading / Polling -->
    <div v-if="uploading" class="text-center py-8">
      <div class="text-4xl mb-4 animate-spin">⏳</div>
      <p class="text-gray-500">{{ recognitionProgress || 'AI 正在识别中...' }}</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg">
      {{ error }}
    </div>

    <!-- AI Results - Multiple Records -->
    <div v-if="aiResults.length > 0 && !uploading" class="space-y-4">
      <div class="flex items-center gap-2 text-green-600">
        <span class="text-xl">✅</span>
        <span class="font-medium">识别成功</span>
        <span class="text-sm text-gray-500 ml-2">
          共 {{ aiResults.length }} 条记录
        </span>
      </div>

      <!-- Per-record editing cards -->
      <div
        v-for="(result, index) in aiResults"
        :key="index"
        class="bg-white rounded-2xl shadow-sm p-6 space-y-4"
      >
        <div class="flex items-center justify-between">
          <h3 class="font-semibold text-gray-700">记录 {{ index + 1 }}</h3>
          <div class="flex items-center gap-2">
            <!-- Record type toggle -->
            <select
              v-model="forms[index].record_type"
              :class="['text-xs px-2 py-0.5 rounded-full border',
                forms[index].record_type === 'income'
                  ? 'bg-green-100 text-green-700 border-green-300'
                  : 'bg-red-100 text-red-600 border-red-300'
              ]"
            >
              <option value="expense">💸 支出</option>
              <option value="income">💰 退款/收入</option>
            </select>
            <span
              :class="['text-xs px-2 py-0.5 rounded-full',
                (result.confidence || 0) >= 0.85 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              ]"
            >
              置信度: {{ ((result.confidence || 0) * 100).toFixed(0) }}%
            </span>
          </div>
        </div>

        <!-- AI recognized summary -->
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div :class="['p-3 rounded-lg', forms[index].record_type === 'income' ? 'bg-green-50' : 'bg-gray-50']">
            <p class="text-gray-500 text-xs">
              {{ forms[index].record_type === 'income' ? '退款/收入' : '消费金额' }}
            </p>
            <p :class="['font-bold text-lg', forms[index].record_type === 'income' ? 'text-green-600' : 'text-red-600']">
              ¥{{ result.amount?.toFixed(2) || '-' }}
            </p>
          </div>
          <div class="bg-gray-50 p-3 rounded-lg">
            <p class="text-gray-500 text-xs">识别商户</p>
            <p class="font-medium">{{ result.merchant_name || '-' }}</p>
          </div>
          <div class="bg-gray-50 p-3 rounded-lg">
            <p class="text-gray-500 text-xs">识别日期</p>
            <p class="font-medium">{{ result.date || '-' }}</p>
          </div>
          <div class="bg-gray-50 p-3 rounded-lg">
            <p class="text-gray-500 text-xs">建议分类</p>
            <p class="font-medium">{{ result.category_guess || '-' }}</p>
          </div>
        </div>

        <hr class="my-2" />

        <!-- Editable form -->
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">金额 *</label>
              <input
                v-model.number="forms[index].amount"
                type="number"
                step="0.01"
                class="w-full border rounded-lg px-3 py-2"
                required
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">账户 *</label>
              <select
                v-model="forms[index].wallet_id"
                class="w-full border rounded-lg px-3 py-2"
                required
              >
                <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">
                  {{ w.name }}
                </option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
            <select v-model="forms[index].category_id" class="w-full border rounded-lg px-3 py-2">
              <option :value="null">未分类</option>
              <option v-for="c in categoryStore.categories" :key="c.id" :value="c.id">
                {{ c.icon }} {{ c.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">备注</label>
            <input
              v-model="forms[index].note"
              type="text"
              class="w-full border rounded-lg px-3 py-2"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">日期</label>
            <input
              v-model="forms[index].date"
              type="datetime-local"
              class="w-full border rounded-lg px-3 py-2"
            />
          </div>
        </div>
      </div>

      <!-- Save All Button -->
      <button
        @click="handleSaveAll"
        class="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700"
      >
        保存全部 {{ aiResults.length }} 条记录
      </button>
    </div>

    <!-- No results yet -->
    <div v-if="!aiResults.length && !uploading" class="text-center text-gray-500 py-8">
      <p>上传小票图片，AI 自动识别金额、商户等信息</p>
      <p class="text-sm mt-2">支持同时识别多条消费记录</p>
    </div>
  </div>
</template>
