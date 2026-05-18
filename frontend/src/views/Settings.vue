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
  <div class="max-w-2xl mx-auto space-y-8">
    <h1 class="text-4xl font-medium text-gray-900 tracking-tight" style="letter-spacing: -0.4px;">⚙️ 设置</h1>

    <!-- Default Wallet Setting -->
    <div class="bg-white rounded-2xl p-8 border border-gray-100">
      <h2 class="text-xl font-medium text-gray-900 mb-3" style="letter-spacing: -0.32px;">📦 默认账户设置</h2>
      <p class="text-sm text-gray-500 mb-6" style="letter-spacing: 0.16px;">
        选择 AI 识别记账时默认使用的账户。您可以在上传页面单独修改每条记录的账户。
      </p>

      <div class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">默认账户</label>
          <select v-model="selectedWalletId" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all">
            <option :value="null">不设置（每次手动选择）</option>
            <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">
              {{ w.name }}
            </option>
          </select>
        </div>

        <!-- Success/Error Messages -->
        <div v-if="success" class="bg-emerald-50 text-emerald-700 p-4 rounded-xl text-sm border border-emerald-100" style="letter-spacing: 0.16px;">
          {{ success }}
        </div>
        <div v-if="error" class="bg-red-50 text-red-600 p-4 rounded-xl text-sm border border-red-100" style="letter-spacing: 0.16px;">
          {{ error }}
        </div>

        <button
          @click="handleSave"
          :disabled="saving"
          class="w-full py-3.5 bg-gray-900 text-white rounded-full font-medium hover:opacity-85 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed text-base"
        >
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>
    </div>

    <!-- Current User Info -->
    <div class="bg-white rounded-2xl p-8 border border-gray-100">
      <h2 class="text-xl font-medium text-gray-900 mb-6" style="letter-spacing: -0.32px;">👤 账户信息</h2>
      <div class="space-y-4 text-sm">
        <div class="flex justify-between py-3 border-b border-gray-100">
          <span class="text-gray-500" style="letter-spacing: 0.16px;">用户名</span>
          <span class="font-medium text-gray-900">{{ authStore.user?.username }}</span>
        </div>
        <div class="flex justify-between py-3 border-b border-gray-100">
          <span class="text-gray-500" style="letter-spacing: 0.16px;">邮箱</span>
          <span class="font-medium text-gray-900">{{ authStore.user?.email }}</span>
        </div>
        <div class="flex justify-between py-3">
          <span class="text-gray-500" style="letter-spacing: 0.16px;">注册时间</span>
          <span class="font-medium text-gray-900">{{ new Date(authStore.user?.created_at || '').toLocaleDateString('zh-CN') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>