<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { aiApi } from '@/api'

interface RecognizedRecord {
  amount: number
  record_type: string
  merchant_name: string
  date: string
  category_guess: string
  category_id: number | null
  confidence: number
}

interface Job {
  id: number
  original_image_url: string
  status: 'pending' | 'processing' | 'done' | 'failed'
  result_json: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
  records: RecognizedRecord[]
}

interface PendingRecord {
  id: number
  amount: number
  record_type: 'expense' | 'income'
  note: string
  date: string
  category_id: number | null
  original_image_url: string
  ai_confidence: number
  is_ai_recognized: number
  job_id: number
  status: 'pending' | 'confirmed' | 'rejected'
  created_at: string
  updated_at: string
}

const jobs = ref<Job[]>([])
const pendingRecords = ref<PendingRecord[]>([])
const loading = ref(false)
const loadingPending = ref(false)
const expandedId = ref<number | null>(null)
const activeTab = ref<'jobs' | 'pending'>('pending')
const processingRecords = ref<Set<number>>(new Set())

function parseResult(job: Job): RecognizedRecord[] {
  if (!job.result_json) return []
  try {
    const d = JSON.parse(job.result_json)
    return d.records || []
  } catch {
    return []
  }
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    pending: '⏳ 等待中',
    processing: '🔄 识别中',
    done: '✅ 完成',
    failed: '❌ 失败',
  }
  return map[s] || s
}

function statusClass(s: string) {
  const map: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-500',
    processing: 'bg-blue-100 text-blue-700',
    done: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-600',
  }
  return map[s] || ''
}

function formatDate(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

async function refresh() {
  loading.value = true
  try {
    const res = await aiApi.listJobs()
    jobs.value = res.data.map((j: any) => ({
      ...j,
      records: parseResult(j),
    }))
  } finally {
    loading.value = false
  }
}

async function refreshPending() {
  loadingPending.value = true
  try {
    const res = await aiApi.listPendingRecords()
    pendingRecords.value = res.data
  } finally {
    loadingPending.value = false
  }
}

async function confirmRecord(recordId: number) {
  if (processingRecords.value.has(recordId)) return
  processingRecords.value.add(recordId)
  try {
    await aiApi.confirmRecord(recordId)
    pendingRecords.value = pendingRecords.value.filter(r => r.id !== recordId)
  } catch (e: any) {
    alert('确认失败：' + (e.response?.data?.detail || e.message))
  } finally {
    processingRecords.value.delete(recordId)
  }
}

async function rejectRecord(recordId: number) {
  if (processingRecords.value.has(recordId)) return
  processingRecords.value.add(recordId)
  try {
    await aiApi.rejectRecord(recordId)
    pendingRecords.value = pendingRecords.value.filter(r => r.id !== recordId)
  } catch (e: any) {
    alert('拒绝失败：' + (e.response?.data?.detail || e.message))
  } finally {
    processingRecords.value.delete(recordId)
  }
}

onMounted(() => {
  refreshPending()
  refresh()
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-800">🤖 AI 识别记录</h1>
      <button
        @click="refresh(); refreshPending()"
        class="text-sm text-indigo-600 hover:text-indigo-800"
        :disabled="loading || loadingPending"
      >
        {{ loading || loadingPending ? '加载中...' : '🔄 刷新' }}
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex border-b border-gray-200">
      <button
        @click="activeTab = 'pending'"
        :class="[
          'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
          activeTab === 'pending'
            ? 'border-indigo-500 text-indigo-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        ]"
      >
        待确认 ({{ pendingRecords.length }})
      </button>
      <button
        @click="activeTab = 'jobs'"
        :class="[
          'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
          activeTab === 'jobs'
            ? 'border-indigo-500 text-indigo-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        ]"
      >
        识别记录 ({{ jobs.length }})
      </button>
    </div>

    <!-- Pending records tab -->
    <div v-if="activeTab === 'pending'" class="space-y-3">
      <!-- Empty state -->
      <div v-if="!loadingPending && pendingRecords.length === 0" class="text-center py-16 text-gray-400">
        <div class="text-5xl mb-3">✅</div>
        <p>没有待确认的记录</p>
        <p class="text-sm mt-1">所有 AI 识别记录已处理完成</p>
      </div>

      <!-- Pending record cards -->
      <div
        v-for="record in pendingRecords"
        :key="record.id"
        class="bg-white rounded-2xl shadow-sm overflow-hidden border-2 border-yellow-200"
      >
        <div class="p-4 space-y-3">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-700">记录 #{{ record.id }}</span>
              <span class="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
                ⏳ 待确认
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span
                :class="[
                  'text-xs px-2 py-0.5 rounded-full',
                  record.record_type === 'income' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                ]"
              >
                {{ record.record_type === 'income' ? '💰 收入' : '💸 支出' }}
              </span>
              <span
                :class="[
                  'text-xs px-2 py-0.5 rounded-full',
                  (record.ai_confidence || 0) >= 0.85 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                ]"
              >
                置信度 {{ ((record.ai_confidence || 0) * 100).toFixed(0) }}%
              </span>
            </div>
          </div>

          <!-- Details grid -->
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div class="p-2 bg-gray-50 rounded-lg">
              <p class="text-gray-400 text-xs">金额</p>
              <p :class="['font-bold', record.record_type === 'income' ? 'text-green-600' : 'text-red-600']">
                ¥{{ record.amount?.toFixed(2) || '-' }}
              </p>
            </div>
            <div class="p-2 bg-gray-50 rounded-lg">
              <p class="text-gray-400 text-xs">商户/备注</p>
              <p class="font-medium">{{ record.note || '-' }}</p>
            </div>
            <div class="p-2 bg-gray-50 rounded-lg">
              <p class="text-gray-400 text-xs">日期</p>
              <p class="font-medium">{{ record.date ? new Date(record.date).toLocaleString('zh-CN') : '-' }}</p>
            </div>
            <div class="p-2 bg-gray-50 rounded-lg">
              <p class="text-gray-400 text-xs">分类</p>
              <p class="font-medium">{{ record.category_id ? '已匹配' : '未匹配' }}</p>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-2 pt-2">
            <button
              @click="confirmRecord(record.id)"
              :disabled="processingRecords.has(record.id)"
              class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {{ processingRecords.has(record.id) ? '处理中...' : '✅ 确认保存' }}
            </button>
            <button
              @click="rejectRecord(record.id)"
              :disabled="processingRecords.has(record.id)"
              class="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {{ processingRecords.has(record.id) ? '处理中...' : '❌ 丢弃' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Jobs tab -->
    <div v-if="activeTab === 'jobs'" class="space-y-3">
      <!-- Empty state -->
      <div v-if="!loading && jobs.length === 0" class="text-center py-16 text-gray-400">
        <div class="text-5xl mb-3">🧾</div>
        <p>暂无识别记录</p>
        <p class="text-sm mt-1">上传小票图片开始 AI 识别</p>
        <button @click="$router.push('/upload')" class="mt-4 text-indigo-600 text-sm">
          → 去上传
        </button>
      </div>

      <!-- Job list -->
      <div v-for="job in jobs" :key="job.id" class="bg-white rounded-2xl shadow-sm overflow-hidden">
        <!-- Header row -->
        <div
          class="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
          @click="toggleExpand(job.id)"
        >
          <div class="flex items-center gap-3">
            <!-- Thumbnail -->
            <div class="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
              <img
                v-if="job.original_image_url"
                :src="'http://localhost:8000' + job.original_image_url"
                class="w-full h-full object-cover"
                @error="(e) => (e.target as any).style.display = 'none'"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-xl">📄</div>
            </div>

            <div>
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-700">#{{ job.id }}</span>
                <span :class="['text-xs px-2 py-0.5 rounded-full', statusClass(job.status)]">
                  {{ statusLabel(job.status) }}
                </span>
              </div>
              <p class="text-xs text-gray-400 mt-0.5">{{ formatDate(job.created_at) }}</p>
            </div>
          </div>

          <!-- Summary -->
          <div class="flex items-center gap-4">
            <div v-if="job.status === 'done' && job.records.length > 0" class="text-right">
              <p class="text-sm font-medium text-gray-700">
                {{ job.records.length }} 条记录
              </p>
              <p class="text-xs text-gray-400">
                置信度 {{ ((job.records[0]?.confidence || 0) * 100).toFixed(0) }}%
              </p>
            </div>
            <div v-else-if="job.status === 'failed'" class="text-right">
              <p class="text-sm text-red-500">识别失败</p>
            </div>
            <span class="text-gray-300 text-lg">›</span>
          </div>
        </div>

        <!-- Expanded detail -->
        <div v-if="expandedId === job.id" class="border-t px-4 pb-4">
          <!-- Error message -->
          <div v-if="job.status === 'failed'" class="mt-3 p-3 bg-red-50 text-red-600 text-sm rounded-lg">
            {{ job.error_message || '识别过程出错' }}
          </div>

          <!-- Processing / pending -->
          <div v-else-if="job.status === 'pending' || job.status === 'processing'"
               class="mt-3 text-center py-6 text-gray-400">
            <div class="text-2xl animate-pulse">⏳</div>
            <p class="text-sm mt-2">
              {{ job.status === 'processing' ? 'AI 正在识别中，请稍候...' : '排队中...' }}
            </p>
          </div>

          <!-- Done: records -->
          <div v-else-if="job.status === 'done'">
            <div v-if="job.records.length === 0" class="mt-3 text-center py-4 text-gray-400 text-sm">
              未识别出消费记录
            </div>
            <div v-else class="mt-3 space-y-3">
              <div
                v-for="(rec, idx) in job.records"
                :key="idx"
                class="bg-gray-50 rounded-xl p-3 space-y-1"
              >
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium">记录 {{ idx + 1 }}</span>
                  <div class="flex items-center gap-2">
                    <span
                      :class="['text-xs px-2 py-0.5 rounded-full',
                        rec.record_type === 'income' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                      ]"
                    >
                      {{ rec.record_type === 'income' ? '💰 退款/收入' : '💸 支出' }}
                    </span>
                    <span
                      :class="['text-xs px-2 py-0.5 rounded-full',
                        (rec.confidence || 0) >= 0.85 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                      ]"
                    >
                      {{ ((rec.confidence || 0) * 100).toFixed(0) }}%
                    </span>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                  <div class="p-2 bg-white rounded-lg">
                    <p class="text-gray-400 text-xs">金额</p>
                    <p :class="['font-bold', rec.record_type === 'income' ? 'text-green-600' : 'text-red-600']">
                      ¥{{ rec.amount?.toFixed(2) || '-' }}
                    </p>
                  </div>
                  <div class="p-2 bg-white rounded-lg">
                    <p class="text-gray-400 text-xs">商户</p>
                    <p class="font-medium">{{ rec.merchant_name || '-' }}</p>
                  </div>
                  <div class="p-2 bg-white rounded-lg">
                    <p class="text-gray-400 text-xs">日期</p>
                    <p class="font-medium">{{ rec.date || '-' }}</p>
                  </div>
                  <div class="p-2 bg-white rounded-lg">
                    <p class="text-gray-400 text-xs">建议分类</p>
                    <p class="font-medium">{{ rec.category_guess || '-' }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
