<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRecordStore } from '@/stores/record'
import { useWalletStore } from '@/stores/wallet'
import { useCategoryStore } from '@/stores/category'
import { aiApi } from '@/api'
import { RecordType } from '@/types'
import type { AIRecognizeResponse } from '@/types'

const router = useRouter()
const recordStore = useRecordStore()
const walletStore = useWalletStore()
const categoryStore = useCategoryStore()

const fileInput = ref<HTMLInputElement>()
const preview = ref<string | null>(null)
const uploading = ref(false)
const aiResult = ref<AIRecognizeResponse | null>(null)
const error = ref('')

const form = ref({
  wallet_id: 0,
  category_id: null as number | null,
  amount: 0,
  note: '',
  date: new Date().toISOString().slice(0, 16),
})

async function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // Preview
  preview.value = URL.createObjectURL(file)

  // Reset previous result
  aiResult.value = null
  error.value = ''

  // Upload and recognize
  uploading.value = true
  try {
    const res = await aiApi.recognize(file)
    aiResult.value = res.data
    if (res.data.amount) form.value.amount = res.data.amount
    if (res.data.merchant_name) form.value.note = res.data.merchant_name
    if (res.data.category_id) form.value.category_id = res.data.category_id
  } catch (e: any) {
    error.value = e.response?.data?.detail || '识别失败，请重试'
  } finally {
    uploading.value = false
  }
}

async function handleSubmit() {
  if (!aiResult.value) return

  await recordStore.createRecord({
    wallet_id: form.value.wallet_id,
    category_id: form.value.category_id,
    amount: form.value.amount,
    record_type: RecordType.EXPENSE,
    note: form.value.note,
    date: new Date(form.value.date).toISOString(),
  })

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
    form.value.wallet_id = walletStore.wallets[0].id
  }
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-800">🤖 AI 识别记账</h1>

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
      <img v-else :src="preview" class="max-h-64 mx-auto rounded-lg" alt="Preview" />
    </div>

    <div v-if="uploading" class="text-center py-8">
      <div class="text-4xl mb-4 animate-spin">⏳</div>
      <p class="text-gray-500">AI 正在识别中...</p>
    </div>

    <div v-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg">
      {{ error }}
    </div>

    <div v-if="aiResult && !uploading" class="bg-white rounded-2xl shadow-sm p-6 space-y-6">
      <div class="flex items-center gap-2 text-green-600">
        <span class="text-xl">✅</span>
        <span class="font-medium">识别成功</span>
        <span class="text-sm text-gray-500 ml-2">
          置信度: {{ (aiResult.confidence * 100).toFixed(0) }}%
        </span>
      </div>

      <div class="grid grid-cols-2 gap-4 text-sm">
        <div class="bg-gray-50 p-3 rounded-lg">
          <p class="text-gray-500">识别金额</p>
          <p class="font-bold text-lg">¥{{ aiResult.amount?.toFixed(2) || '-' }}</p>
        </div>
        <div class="bg-gray-50 p-3 rounded-lg">
          <p class="text-gray-500">商户</p>
          <p class="font-medium">{{ aiResult.merchant_name || '-' }}</p>
        </div>
        <div class="bg-gray-50 p-3 rounded-lg">
          <p class="text-gray-500">日期</p>
          <p class="font-medium">{{ aiResult.date || '-' }}</p>
        </div>
        <div class="bg-gray-50 p-3 rounded-lg">
          <p class="text-gray-500">建议分类</p>
          <p class="font-medium">{{ aiResult.category_guess || '-' }}</p>
        </div>
      </div>

      <hr class="my-4" />

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">确认金额 *</label>
          <input v-model.number="form.amount" type="number" step="0.01" class="w-full border rounded-lg px-3 py-2" required />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">账户 *</label>
          <select v-model="form.wallet_id" class="w-full border rounded-lg px-3 py-2" required>
            <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
          <select v-model="form.category_id" class="w-full border rounded-lg px-3 py-2">
            <option :value="null">未分类</option>
            <option v-for="c in categoryStore.categories" :key="c.id" :value="c.id">
              {{ c.icon }} {{ c.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">备注</label>
          <input v-model="form.note" type="text" class="w-full border rounded-lg px-3 py-2" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">日期</label>
          <input v-model="form.date" type="datetime-local" class="w-full border rounded-lg px-3 py-2" />
        </div>
        <button
          type="submit"
          :disabled="aiResult.confidence < 0.5"
          class="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {{ aiResult.confidence >= 0.85 ? '直接保存' : '保存到待确认' }}
        </button>
      </form>
    </div>

    <div v-if="!aiResult && !uploading" class="text-center text-gray-500 py-8">
      <p>上传小票图片，AI 自动识别金额、商户等信息</p>
      <p class="text-sm mt-2">置信度 ≥ 85% 自动确认，否则进入待确认列表</p>
    </div>
  </div>
</template>
