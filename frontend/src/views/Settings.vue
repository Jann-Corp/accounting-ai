<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useWalletStore } from '@/stores/wallet'
import { useRouter } from 'vue-router'

const router = useRouter()
const authStore = useAuthStore()
const walletStore = useWalletStore()

const saving = ref(false)
const error = ref('')
const success = ref('')
const selectedWalletId = ref<number | null>(null)

async function handleSave() {
  saving.value = true
  error.value = ''
  success.value = ''
  
  try {
    await authStore.updateDefaultWallet(selectedWalletId.value)
    success.value = '设置已保存'
  } catch (e: any) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await walletStore.fetchWallets()
  // Load current default wallet
  if (authStore.user?.default_wallet_id) {
    selectedWalletId.value = authStore.user.default_wallet_id
  }
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-800">⚙️ 设置</h1>

    <!-- Default Wallet Setting -->
    <div class="bg-white rounded-2xl shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">📦 默认账户设置</h2>
      <p class="text-sm text-gray-500 mb-4">
        选择 AI 识别记账时默认使用的账户。您可以在上传页面单独修改每条记录的账户。
      </p>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">默认账户</label>
          <select v-model="selectedWalletId" class="w-full border rounded-lg px-3 py-2">
            <option :value="null">不设置（每次手动选择）</option>
            <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">
              {{ w.name }}
            </option>
          </select>
        </div>

        <!-- Success/Error Messages -->
        <div v-if="success" class="bg-green-50 text-green-600 p-3 rounded-lg text-sm">
          {{ success }}
        </div>
        <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
          {{ error }}
        </div>

        <button
          @click="handleSave"
          :disabled="saving"
          class="w-full py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>
    </div>

    <!-- Current User Info -->
    <div class="bg-white rounded-2xl shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">👤 账户信息</h2>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between py-2 border-b">
          <span class="text-gray-500">用户名</span>
          <span class="font-medium">{{ authStore.user?.username }}</span>
        </div>
        <div class="flex justify-between py-2 border-b">
          <span class="text-gray-500">邮箱</span>
          <span class="font-medium">{{ authStore.user?.email }}</span>
        </div>
        <div class="flex justify-between py-2">
          <span class="text-gray-500">注册时间</span>
          <span class="font-medium">{{ new Date(authStore.user?.created_at || '').toLocaleDateString('zh-CN') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
