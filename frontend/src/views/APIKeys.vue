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
        <h1 class="text-2xl font-bold" style="color: var(--text-primary);">🔑 API 密钥</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">用于第三方应用接入流水上传接口</p>
      </div>
      <button @click="showModal = true" class="btn-gold">
        + 新建 Key
      </button>
    </div>

    <!-- Tip -->
    <div
      class="rounded-xl p-4 text-sm"
      style="background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2); color: #3B82F6;"
    >
      <p class="font-medium mb-1">💡 使用方式</p>
      <p>调用 <code class="px-1 rounded text-xs" style="background: rgba(59,130,246,0.15);">POST /api/v1/ai/recognize</code> 时，在 HTTP 头中加入：</p>
      <p class="mt-1 font-mono text-xs rounded px-2 py-1" style="background: rgba(59,130,246,0.15);">X-API-Key: ak_your_key_here</p>
    </div>

    <!-- Key List -->
    <div
      class="rounded-2xl overflow-hidden"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
    >
      <div
        v-if="apiKeyStore.loading"
        class="text-center py-12"
        style="color: var(--text-muted);"
      >
        加载中...
      </div>
      <div
        v-else-if="apiKeyStore.apiKeys.length === 0"
        class="text-center py-12"
        style="color: var(--text-muted);"
      >
        还没有 API Key，点击右上角创建
      </div>
      <div v-else>
        <div
          v-for="(key, i) in apiKeyStore.apiKeys"
          :key="key.id"
          class="p-4 transition"
          :style="i > 0 ? 'border-top: 1px solid var(--border-color);' : ''"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <p class="font-medium" style="color: var(--text-primary);">{{ key.name }}</p>
                <span
                  class="text-xs px-2 py-0.5 rounded-full"
                  :style="
                    key.is_active
                      ? 'background: rgba(34,197,94,0.1); color: var(--income-color);'
                      : 'background: var(--bg-hover); color: var(--text-muted);'
                  "
                >
                  {{ key.is_active ? '启用' : '已禁用' }}
                </span>
              </div>
              <p class="text-xs font-mono mt-1" style="color: var(--text-muted);">{{ key.key_prefix }}••••••••</p>
              <div class="flex gap-4 mt-2 text-xs" style="color: var(--text-muted);">
                <span>创建于 {{ formatDate(key.created_at) }}</span>
                <span v-if="key.last_used_at">最后使用 {{ formatDate(key.last_used_at) }}</span>
                <span v-else>从未使用</span>
                <span>过期时间 {{ formatExpiry(key.expires_at) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <button
                @click="handleToggle(key.id, key.is_active)"
                class="text-sm px-3 py-1 rounded-lg border transition"
                :style="
                  key.is_active
                    ? 'border-color: var(--border-color); color: var(--text-secondary);'
                    : 'border-color: var(--income-color); color: var(--income-color);'
                "
              >
                {{ key.is_active ? '禁用' : '启用' }}
              </button>
              <button
                @click="handleDelete(key.id)"
                class="p-2 rounded-lg transition"
                style="color: var(--text-muted);"
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
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay"
      @click.self="showModal = false"
    >
      <div
        class="rounded-2xl p-6 w-full max-w-md"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);"
      >
        <h2 class="text-xl font-bold mb-6" style="color: var(--text-primary);">新建 API Key</h2>
        <form @submit.prevent="handleCreate" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">Key 名称</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="例如：支付宝自动同步"
              class="input-gold"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">过期时间（可选）</label>
            <input
              v-model="form.expires_at"
              type="datetime-local"
              class="input-gold"
            />
            <p class="text-xs mt-1" style="color: var(--text-muted);">留空表示永不过期</p>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-2.5 rounded-xl border" style="border-color: var(--border-color); color: var(--text-secondary);">
              取消
            </button>
            <button type="submit" :disabled="creating" class="flex-1 btn-gold">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Show Key Once Modal -->
    <div
      v-if="showKeyModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay"
    >
      <div
        class="rounded-2xl p-6 w-full max-w-md"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);"
      >
        <div class="text-center mb-4">
          <div class="text-5xl mb-3">🔑</div>
          <h2 class="text-xl font-bold" style="color: var(--text-primary);">API Key 已创建</h2>
          <p class="text-sm mt-1" style="color: var(--expense-color);">⚠️ Key 仅显示一次，请立即复制保存！</p>
        </div>
        <div
          class="rounded-xl p-3 font-mono text-sm break-all"
          style="background: var(--bg-hover); color: var(--text-primary);"
        >
          {{ newKey }}
        </div>
        <div
          class="mt-4 p-3 rounded-xl text-xs"
          style="background: var(--accent-gold-light); color: var(--accent-gold-dark); border: 1px solid rgba(212,168,67,0.3);"
        >
          请妥善保管此 Key，不要泄露给他人。如若泄露，请立即删除并重新创建。
        </div>
        <button
          @click="showKeyModal = false"
          class="w-full mt-4 btn-gold"
        >
          我已保存
        </button>
      </div>
    </div>
  </div>
</template>
