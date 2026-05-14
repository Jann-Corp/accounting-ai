<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { aiApi } from '@/api'
import { useAIRecordStore } from '@/stores/aiRecord'

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

const jobs = ref<Job[]>([])
const loading = ref(false)
const loadingPending = ref(false)
const expandedId = ref<number | null>(null)
const activeTab = ref<'jobs' | 'pending'>('pending')
const processingRecords = ref<Set<number>>(new Set())

const aiRecordStore = useAIRecordStore()
const pendingRecords = aiRecordStore.pendingRecords

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
    await aiRecordStore.fetchPendingRecords()
  } finally {
    loadingPending.value = false
  }
}

async function confirmRecord(recordId: number) {
  if (processingRecords.value.has(recordId)) return
  processingRecords.value.add(recordId)
  try {
    await aiRecordStore.confirmRecord(recordId)
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
    await aiRecordStore.rejectRecord(recordId)
  } catch (e: any) {
    alert('拒绝失败：' + (e.response?.data?.detail || e.message))
  } finally {
    processingRecords.value.delete(recordId)
  }
}

onMounted(() => {
  refreshPending()
  refresh()
  aiRecordStore.markAsViewed()
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold" style="color: var(--text-primary);">🤖 AI 识别记录</h1>
      <button
        @click="refresh(); refreshPending()"
        class="text-sm font-medium"
        style="color: var(--accent-gold);"
        :disabled="loading || loadingPending"
      >
        {{ loading || loadingPending ? '加载中...' : '🔄 刷新' }}
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex rounded-xl overflow-hidden" style="background: var(--bg-card); border: 1px solid var(--border-color);">
      <button
        v-for="tab in [
          { value: 'pending', label: '待确认', count: pendingRecords.length },
          { value: 'jobs', label: '识别记录', count: jobs.length },
        ]"
        :key="tab.value"
        @click="activeTab = tab.value as any"
        class="flex-1 py-3 text-sm font-medium transition"
        :style="
          activeTab === tab.value
            ? 'background: var(--accent-gold); color: #1C1917;'
            : 'color: var(--text-muted);'
        "
      >
        {{ tab.label }} ({{ tab.count }})
      </button>
    </div>

    <!-- Pending records tab -->
    <div v-if="activeTab === 'pending'" class="space-y-3">
      <!-- Empty state -->
      <div
        v-if="!loadingPending && pendingRecords.length === 0"
        class="text-center py-16 rounded-2xl"
        style="color: var(--text-muted); background: var(--bg-card); border: 1px solid var(--border-color);"
      >
        <div class="text-5xl mb-3">✅</div>
        <p>没有待确认的记录</p>
        <p class="text-sm mt-1">所有 AI 识别记录已处理完成</p>
      </div>

      <!-- Pending record cards -->
      <div
        v-for="record in pendingRecords"
        :key="record.id"
        class="rounded-2xl overflow-hidden"
        style="background: var(--bg-card); border: 2px solid var(--accent-gold); box-shadow: var(--shadow-md);"
      >
        <div class="p-4 space-y-3">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium" style="color: var(--text-secondary);">记录 #{{ record.id }}</span>
              <span
                v-if="record.is_suspected_duplicate"
                class="text-xs px-2 py-0.5 rounded-full"
                style="background: rgba(249,115,22,0.1); color: #F97316;"
              >
                ⚠️ 疑似重复
              </span>
              <span
                v-else
                class="text-xs px-2 py-0.5 rounded-full"
                style="background: var(--accent-gold-light); color: var(--accent-gold);"
              >
                ⏳ 待确认
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span
                class="text-xs px-2 py-0.5 rounded-full"
                :style="record.record_type === 'income'
                  ? 'background: rgba(34,197,94,0.1); color: var(--income-color);'
                  : 'background: rgba(239,68,68,0.1); color: var(--expense-color);'"
              >
                {{ record.record_type === 'income' ? '💰 收入' : '💸 支出' }}
              </span>
              <span
                class="text-xs px-2 py-0.5 rounded-full"
                :style="(record.ai_confidence || 0) >= 0.85
                  ? 'background: rgba(34,197,94,0.1); color: var(--income-color);'
                  : 'background: var(--accent-gold-light); color: var(--accent-gold);'"
              >
                置信度 {{ ((record.ai_confidence || 0) * 100).toFixed(0) }}%
              </span>
            </div>
          </div>

          <!-- Details grid -->
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div class="p-2 rounded-lg" style="background: var(--bg-hover);">
              <p class="text-xs" style="color: var(--text-muted);">金额</p>
              <p
                class="font-bold"
                :style="{ color: record.record_type === 'income' ? 'var(--income-color)' : 'var(--expense-color)' }"
              >
                ¥{{ record.amount?.toFixed(2) || '-' }}
              </p>
            </div>
            <div class="p-2 rounded-lg" style="background: var(--bg-hover);">
              <p class="text-xs" style="color: var(--text-muted);">商户/备注</p>
              <p class="font-medium" style="color: var(--text-primary);">{{ record.note || '-' }}</p>
            </div>
            <div class="p-2 rounded-lg" style="background: var(--bg-hover);">
              <p class="text-xs" style="color: var(--text-muted);">日期</p>
              <p class="font-medium" style="color: var(--text-primary);">
                {{ record.date ? new Date(record.date).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }) : '-' }}
              </p>
            </div>
            <div class="p-2 rounded-lg" style="background: var(--bg-hover);">
              <p class="text-xs" style="color: var(--text-muted);">分类</p>
              <p class="font-medium" style="color: var(--text-primary);">{{ record.category_id ? '已匹配' : '未匹配' }}</p>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-2 pt-2">
            <button
              @click="confirmRecord(record.id)"
              :disabled="processingRecords.has(record.id)"
              class="flex-1 py-2.5 rounded-xl font-medium transition"
              style="background: var(--income-color); color: white;"
            >
              {{ processingRecords.has(record.id) ? '处理中...' : '✅ 确认保存' }}
            </button>
            <button
              @click="rejectRecord(record.id)"
              :disabled="processingRecords.has(record.id)"
              class="flex-1 py-2.5 rounded-xl transition"
              style="background: var(--bg-hover); color: var(--text-secondary);"
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
      <div
        v-if="!loading && jobs.length === 0"
        class="text-center py-16 rounded-2xl"
        style="color: var(--text-muted); background: var(--bg-card); border: 1px solid var(--border-color);"
      >
        <div class="text-5xl mb-3">🧾</div>
        <p>暂无识别记录</p>
        <p class="text-sm mt-1">上传小票图片开始 AI 识别</p>
        <button @click="$router.push('/upload')" class="mt-4 text-sm font-medium" style="color: var(--accent-gold);">
          → 去上传
        </button>
      </div>

      <!-- Job list -->
      <div
        v-for="job in jobs"
        :key="job.id"
        class="rounded-2xl overflow-hidden"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
      >
        <!-- Header row -->
        <div
          class="flex items-center justify-between p-4 cursor-pointer transition"
          style="border-bottom: 1px solid var(--border-color);"
          @click="toggleExpand(job.id)"
        >
          <div class="flex items-center gap-3">
            <!-- Thumbnail -->
            <div
              class="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0"
              style="background: var(--bg-hover);"
            >
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
                <span class="text-sm font-medium" style="color: var(--text-primary);">#{{ job.id }}</span>
                <span
                  class="text-xs px-2 py-0.5 rounded-full"
                  :style="
                    job.status === 'done'
                      ? 'background: rgba(34,197,94,0.1); color: var(--income-color);'
                      : job.status === 'failed'
                      ? 'background: rgba(239,68,68,0.1); color: var(--expense-color);'
                      : job.status === 'processing'
                      ? 'background: rgba(59,130,246,0.1); color: #3B82F6;'
                      : 'background: var(--bg-hover); color: var(--text-muted);'
                  "
                >
                  {{ statusLabel(job.status) }}
                </span>
              </div>
              <p class="text-xs mt-0.5" style="color: var(--text-muted);">{{ formatDate(job.created_at) }}</p>
            </div>
          </div>

          <!-- Summary -->
          <div class="flex items-center gap-4">
            <div v-if="job.status === 'done' && job.records.length > 0" class="text-right">
              <p class="text-sm font-medium" style="color: var(--text-primary);">
                {{ job.records.length }} 条记录
              </p>
              <p class="text-xs" style="color: var(--text-muted);">
                置信度 {{ ((job.records[0]?.confidence || 0) * 100).toFixed(0) }}%
              </p>
            </div>
            <div v-else-if="job.status === 'failed'" class="text-right">
              <p class="text-sm" style="color: var(--expense-color);">识别失败</p>
            </div>
            <span class="text-xl" style="color: var(--text-muted);">›</span>
          </div>
        </div>

        <!-- Expanded detail -->
        <div v-if="expandedId === job.id" class="px-4 pb-4">
          <!-- Error message -->
          <div
            v-if="job.status === 'failed'"
            class="mt-3 p-3 rounded-xl text-sm"
            style="background: rgba(239,68,68,0.1); color: var(--expense-color); border: 1px solid rgba(239,68,68,0.2);"
          >
            {{ job.error_message || '识别过程出错' }}
          </div>

          <!-- Processing / pending -->
          <div
            v-else-if="job.status === 'pending' || job.status === 'processing'"
            class="mt-3 text-center py-6"
            style="color: var(--text-muted);"
          >
            <div class="text-2xl animate-pulse">⏳</div>
            <p class="text-sm mt-2">
              {{ job.status === 'processing' ? 'AI 正在识别中，请稍候...' : '排队中...' }}
            </p>
          </div>

          <!-- Done: records -->
          <div v-else-if="job.status === 'done'">
            <div
              v-if="job.records.length === 0"
              class="mt-3 text-center py-4 text-sm"
              style="color: var(--text-muted);"
            >
              未识别出消费记录
            </div>
            <div v-else class="mt-3 space-y-3">
              <div
                v-for="(rec, idx) in job.records"
                :key="idx"
                class="rounded-xl p-3 space-y-1"
                style="background: var(--bg-hover);"
              >
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium" style="color: var(--text-primary);">记录 {{ idx + 1 }}</span>
                  <div class="flex items-center gap-2">
                    <span
                      class="text-xs px-2 py-0.5 rounded-full"
                      :style="
                        rec.record_type === 'income'
                          ? 'background: rgba(34,197,94,0.1); color: var(--income-color);'
                          : 'background: rgba(239,68,68,0.1); color: var(--expense-color);'
                      "
                    >
                      {{ rec.record_type === 'income' ? '💰 退款/收入' : '💸 支出' }}
                    </span>
                    <span
                      class="text-xs px-2 py-0.5 rounded-full"
                      :style="
                        (rec.confidence || 0) >= 0.85
                          ? 'background: rgba(34,197,94,0.1); color: var(--income-color);'
                          : 'background: var(--accent-gold-light); color: var(--accent-gold);'
                      "
                    >
                      {{ ((rec.confidence || 0) * 100).toFixed(0) }}%
                    </span>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                  <div class="p-2 rounded-lg" style="background: var(--bg-card);">
                    <p class="text-xs" style="color: var(--text-muted);">金额</p>
                    <p
                      class="font-bold"
                      :style="{ color: rec.record_type === 'income' ? 'var(--income-color)' : 'var(--expense-color)' }"
                    >
                      ¥{{ rec.amount?.toFixed(2) || '-' }}
                    </p>
                  </div>
                  <div class="p-2 rounded-lg" style="background: var(--bg-card);">
                    <p class="text-xs" style="color: var(--text-muted);">商户</p>
                    <p class="font-medium" style="color: var(--text-primary);">{{ rec.merchant_name || '-' }}</p>
                  </div>
                  <div class="p-2 rounded-lg" style="background: var(--bg-card);">
                    <p class="text-xs" style="color: var(--text-muted);">日期</p>
                    <p class="font-medium" style="color: var(--text-primary);">{{ rec.date || '-' }}</p>
                  </div>
                  <div class="p-2 rounded-lg" style="background: var(--bg-card);">
                    <p class="text-xs" style="color: var(--text-muted);">建议分类</p>
                    <p class="font-medium" style="color: var(--text-primary);">{{ rec.category_guess || '-' }}</p>
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
