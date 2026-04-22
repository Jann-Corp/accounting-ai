<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApiKeyStore } from '@/stores/apikey'
import type { ApiKeyCreate } from '@/types'

const apiKeyStore = useApiKeyStore()

const showModal = ref(false)
const showKeyModal = ref(false)
const newKey = ref('')
const form = ref<ApiKeyCreate>({
  name: '',
  expires_at: null,
})
const creating = ref(false)

onMounted(() => {
  apiKeyStore.fetchApiKeys()
})

async function handleCreate() {
  creating.value = true
  try {
    const result = await apiKeyStore.createApiKey(form.value)
    // Show the full key once
    newKey.value = result.key_full || ''
    showModal.value = false
    showKeyModal.value = true
    form.value = { name: '', expires_at: null }
  } catch (error: any) {
    console.error('Failed to create API key:', error)
    alert('创建失败：' + (error.response?.data?.detail || error.message || '未知错误'))
  } finally {
    creating.value = false
  }
}

async function handleDelete(id: number) {
  if (confirm('确定要删除这个 API Key 吗？删除后所有使用该 Key 的调用将立即失效。')) {
    await apiKeyStore.deleteApiKey(id)
  }
}

async function handleToggle(id: number, current: boolean) {
  await apiKeyStore.toggleApiKey(id, !current)
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

function formatExpiry(dateStr: string | null) {
  if (!dateStr) return '永不过期'
  const d = new Date(dateStr)
  const now = new Date()
  if (d < now) return `已过期 (${formatDate(dateStr)})`
  return formatDate(dateStr)
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">🔑 API 密钥</h1>
        <p class="text-sm text-gray-500 mt-1">用于第三方应用接入流水上传接口</p>
      </div>
      <button
        @click="showModal = true"
        class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
      >
        + 新建 Key
      </button>
    </div>

    <!-- Tip -->
    <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-700">
      <p class="font-medium mb-1">💡 使用方式</p>
      <p>调用 <code class="bg-blue-100 px-1 rounded">POST /api/v1/ai/recognize</code> 时，在 HTTP 头中加入：</p>
      <p class="mt-1 font-mono text-xs bg-blue-100 rounded px-2 py-1">X-API-Key: ak_your_key_here</p>
    </div>

    <!-- Key List -->
    <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
      <div v-if="apiKeyStore.loading" class="text-center py-12 text-gray-500">加载中...</div>
      <div v-else-if="apiKeyStore.apiKeys.length === 0" class="text-center py-12 text-gray-500">
        还没有 API Key，点击右上角创建
      </div>
      <div v-else class="divide-y">
        <div
          v-for="key in apiKeyStore.apiKeys"
          :key="key.id"
          class="p-4 hover:bg-gray-50"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <p class="font-medium text-gray-800">{{ key.name }}</p>
                <span
                  :class="['text-xs px-2 py-0.5 rounded-full', key.is_active
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-500']"
                >
                  {{ key.is_active ? '启用' : '已禁用' }}
                </span>
              </div>
              <p class="text-xs font-mono text-gray-400 mt-1">{{ key.key_prefix }}••••••••</p>
              <div class="flex gap-4 mt-2 text-xs text-gray-500">
                <span>创建于 {{ formatDate(key.created_at) }}</span>
                <span v-if="key.last_used_at">最后使用 {{ formatDate(key.last_used_at) }}</span>
                <span v-else>从未使用</span>
                <span>过期时间 {{ formatExpiry(key.expires_at) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <!-- Toggle -->
              <button
                @click="handleToggle(key.id, key.is_active)"
                :class="['text-sm px-3 py-1 rounded-lg border',
                  key.is_active
                    ? 'border-gray-300 text-gray-600 hover:bg-gray-100'
                    : 'border-green-300 text-green-600 hover:bg-green-50']"
              >
                {{ key.is_active ? '禁用' : '启用' }}
              </button>
              <!-- Delete -->
              <button
                @click="handleDelete(key.id)"
                class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                title="删除"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">新建 API Key</h2>
        <form @submit.prevent="handleCreate" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Key 名称</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="例如：支付宝自动同步"
              class="w-full border rounded-lg px-3 py-2"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">过期时间（可选）</label>
            <input
              v-model="form.expires_at"
              type="datetime-local"
              class="w-full border rounded-lg px-3 py-2"
            />
            <p class="text-xs text-gray-400 mt-1">留空表示永不过期</p>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-2 border rounded-lg">取消</button>
            <button
              type="submit"
              :disabled="creating"
              class="flex-1 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50"
            >
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Show Key Once Modal -->
    <div v-if="showKeyModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <div class="text-center mb-4">
          <div class="text-5xl mb-3">🔑</div>
          <h2 class="text-xl font-bold text-gray-800">API Key 已创建</h2>
          <p class="text-sm text-red-500 mt-1">⚠️ Key 仅显示一次，请立即复制保存！</p>
        </div>
        <div class="bg-gray-100 rounded-lg p-3 font-mono text-sm break-all text-gray-800">
          {{ newKey }}
        </div>
        <div class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-700">
          请妥善保管此 Key，不要泄露给他人。如若泄露，请立即删除并重新创建。
        </div>
        <button
          @click="showKeyModal = false"
          class="w-full mt-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          我已保存
        </button>
      </div>
    </div>
  </div>
</template>
