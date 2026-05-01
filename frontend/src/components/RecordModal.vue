<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useRecordStore } from '@/stores/record'
import { useWalletStore } from '@/stores/wallet'
import { useCategoryStore } from '@/stores/category'
import { aiApi } from '@/api'
import { RecordType } from '@/types'
import type { AIRecognizeRecord } from '@/types'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const router = useRouter()
const recordStore = useRecordStore()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()

const activeTab = ref<'ai' | 'manual'>('ai')

// AI mode state
const fileInput = ref<HTMLInputElement>()
const preview = ref<string | null>(null)
const uploading = ref(false)
const uploadSuccess = ref(false)
const taskId = ref<string | null>(null)
const pollInterval = ref<ReturnType<typeof setInterval> | null>(null)
const recognitionProgress = ref('')
const error = ref('')

// Manual mode state
const manualForm = ref({
  wallet_id: 0,
  category_id: null as number | null,
  amount: 0,
  record_type: 'expense' as 'expense' | 'income',
  note: '',
  date: '',
})
const manualSaving = ref(false)
const manualError = ref('')

// Filter categories by record type
const filteredCategories = computed(() => {
  if (manualForm.value.record_type === 'income') {
    return categoryStore.categories.filter(c => c.category_type === 'income')
  }
  return categoryStore.categories.filter(c => c.category_type === 'expense')
})

// Reset when modal opens
watch(() => props.show, async (val) => {
  if (val) {
    resetState()
    await Promise.all([
      walletStore.fetchWallets(),
      categoryStore.fetchCategories(),
    ])
    // Set default wallet
    if (walletStore.wallets.length > 0) {
      manualForm.value.wallet_id = walletStore.wallets[0].id
    }
    // Set default date to now
    manualForm.value.date = toLocalDatetimeStr(new Date())
  }
})

function toLocalDatetimeStr(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hour = pad(date.getHours())
  const min = pad(date.getMinutes())
  return `${year}-${month}-${day}T${hour}:${min}`
}

function resetState() {
  activeTab.value = 'ai'
  preview.value = null
  uploading.value = false
  uploadSuccess.value = false
  taskId.value = null
  recognitionProgress.value = ''
  error.value = ''
  manualForm.value = {
    wallet_id: 0,
    category_id: null,
    amount: 0,
    record_type: 'expense',
    note: '',
    date: toLocalDatetimeStr(new Date()),
  }
  manualError.value = ''
}

function stopPolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // Preview
  if (preview.value) URL.revokeObjectURL(preview.value)
  preview.value = URL.createObjectURL(file)
  error.value = ''
  uploadSuccess.value = false
  taskId.value = null

  // Upload and start async recognition
  uploading.value = true
  recognitionProgress.value = '正在上传图片...'
  try {
    const res = await aiApi.recognizeAsync(file)
    const data = res.data
    taskId.value = data.task_id
    uploadSuccess.value = true
    recognitionProgress.value = 'AI 正在识别中...'

    // Start polling
    pollInterval.value = setInterval(async () => {
      try {
        const pollRes = await aiApi.getRecognizeResult(taskId.value!)
        const pollData = pollRes.data

        if (pollData.status === 'pending') {
          recognitionProgress.value = 'AI 正在识别中，请稍候...'
        } else if (pollData.status === 'done') {
          stopPolling()
          recognitionProgress.value = '识别完成！'
          uploading.value = false
        } else {
          stopPolling()
          error.value = '识别失败，请重试'
          uploading.value = false
          uploadSuccess.value = false
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
    uploadSuccess.value = false
    if (fileInput.value) fileInput.value.value = ''
    preview.value = null
  }
}

function handleViewAIRecords() {
  stopPolling()
  emit('close')
  router.push('/ai-records')
}

function handleCloseAIRecordModal() {
  stopPolling()
  uploadSuccess.value = false
  uploading.value = false
  preview.value = null
  if (fileInput.value) fileInput.value.value = ''
  emit('close')
}

async function handleManualSubmit() {
  if (manualForm.value.amount <= 0) {
    manualError.value = '请输入有效金额'
    return
  }
  if (!manualForm.value.wallet_id) {
    manualError.value = '请选择账户'
    return
  }

  manualSaving.value = true
  manualError.value = ''
  try {
    await recordStore.createRecord({
      wallet_id: manualForm.value.wallet_id,
      category_id: manualForm.value.category_id,
      amount: manualForm.value.amount,
      record_type: manualForm.value.record_type === 'income' ? RecordType.INCOME : RecordType.EXPENSE,
      note: manualForm.value.note,
      date: new Date(manualForm.value.date).toISOString(),
    })
    emit('close')
    await recordStore.fetchRecords({ limit: 10 })
  } catch (e: any) {
    manualError.value = e.response?.data?.detail || '保存失败'
  } finally {
    manualSaving.value = false
  }
}

function handleClose() {
  stopPolling()
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="handleClose" />

      <!-- Modal -->
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b">
          <h2 class="text-lg font-semibold text-gray-800">记一笔</h2>
          <button @click="handleClose" class="p-2 hover:bg-gray-100 rounded-lg">
            <span class="text-xl">✕</span>
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex border-b">
          <button
            @click="activeTab = 'ai'"
            :class="['flex-1 py-3 text-center font-medium transition-colors', activeTab === 'ai' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700']"
          >
            🤖 AI 识别
          </button>
          <button
            @click="activeTab = 'manual'"
            :class="['flex-1 py-3 text-center font-medium transition-colors', activeTab === 'manual' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700']"
          >
            ✏️ 手动记账
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-4">
          <!-- AI Tab -->
          <div v-if="activeTab === 'ai'" class="space-y-4">
            <!-- Upload Success Modal -->
            <div v-if="uploadSuccess" class="text-center py-8 space-y-4">
              <div class="text-6xl">🔍</div>
              <div>
                <p class="text-lg font-medium text-gray-700">正在识别中...</p>
                <p class="text-sm text-gray-500 mt-1">{{ recognitionProgress }}</p>
              </div>
              <div class="flex gap-3">
                <button
                  @click="handleViewAIRecords"
                  class="flex-1 py-2 px-4 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700"
                >
                  查看 AI 记录
                </button>
                <button
                  @click="handleCloseAIRecordModal"
                  class="flex-1 py-2 px-4 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
                >
                  我知道了
                </button>
              </div>
            </div>

            <!-- Normal Upload UI -->
            <template v-else>
              <!-- Upload Area -->
              <div
                @click="triggerFileInput"
                class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-indigo-400 transition"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/*"
                  @change="handleFileSelect"
                  class="hidden"
                />
                <div v-if="!preview" class="space-y-3">
                  <div class="text-5xl">📷</div>
                  <div>
                    <p class="text-gray-700 font-medium">点击上传小票图片</p>
                    <p class="text-sm text-gray-500 mt-1">支持 JPG、PNG、WebP 格式</p>
                  </div>
                </div>
                <img v-else :src="preview" class="max-h-48 mx-auto rounded-lg" alt="Preview" />
              </div>

              <!-- Loading -->
              <div v-if="uploading" class="text-center py-4">
                <div class="text-3xl mb-2 animate-spin">⏳</div>
                <p class="text-gray-500">{{ recognitionProgress || '上传中...' }}</p>
              </div>

              <!-- Error -->
              <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                {{ error }}
              </div>
            </template>
          </div>

          <!-- Manual Tab -->
          <div v-if="activeTab === 'manual'" class="space-y-4">
            <!-- Record Type Toggle -->
            <div class="flex gap-2">
              <button
                @click="manualForm.record_type = 'expense'; manualForm.category_id = null"
                :class="['flex-1 py-2 rounded-lg font-medium transition-colors', manualForm.record_type === 'expense' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600']"
              >
                💸 支出
              </button>
              <button
                @click="manualForm.record_type = 'income'; manualForm.category_id = null"
                :class="['flex-1 py-2 rounded-lg font-medium transition-colors', manualForm.record_type === 'income' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600']"
              >
                💰 收入
              </button>
            </div>

            <!-- Amount -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">金额 *</label>
              <input
                v-model.number="manualForm.amount"
                type="number"
                step="0.01"
                placeholder="0.00"
                class="w-full border rounded-lg px-3 py-2 text-lg"
                required
              />
            </div>

            <!-- Wallet -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">账户 *</label>
              <select v-model="manualForm.wallet_id" class="w-full border rounded-lg px-3 py-2" required>
                <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>

            <!-- Category -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
              <select v-model="manualForm.category_id" class="w-full border rounded-lg px-3 py-2">
                <option :value="null">未分类</option>
                <option v-for="c in filteredCategories" :key="c.id" :value="c.id">
                  {{ c.icon }} {{ c.name }}
                </option>
              </select>
            </div>

            <!-- Note -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">备注</label>
              <input
                v-model="manualForm.note"
                type="text"
                placeholder="商家名称或备注"
                class="w-full border rounded-lg px-3 py-2"
              />
            </div>

            <!-- Date -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">日期</label>
              <input
                v-model="manualForm.date"
                type="datetime-local"
                class="w-full border rounded-lg px-3 py-2"
              />
            </div>

            <!-- Error -->
            <div v-if="manualError" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
              {{ manualError }}
            </div>

            <!-- Submit -->
            <button
              @click="handleManualSubmit"
              :disabled="manualSaving"
              class="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {{ manualSaving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
