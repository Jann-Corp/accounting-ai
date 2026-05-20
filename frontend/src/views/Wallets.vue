<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useWalletStore } from '@/stores/wallet'
import { walletApi } from '@/api'
import { WalletType } from '@/types'
import type { WalletCreate } from '@/types'

const walletStore = useWalletStore()

const showModal = ref(false)
const showTransferModal = ref(false)
const editingWallet = ref<WalletCreate | null>(null)
const submitting = ref(false)

// 监听弹窗状态，阻止背景滚动
watch(showModal, (val) => {
  if (val) {
    // 禁止背景滚动
    document.body.style.overflow = 'hidden'
  } else {
    // 恢复背景滚动
    document.body.style.overflow = ''
  }
})

// 监听转账弹窗状态，阻止背景滚动
watch(showTransferModal, (val) => {
  if (val) {
    // 禁止背景滚动
    document.body.style.overflow = 'hidden'
  } else {
    // 恢复背景滚动
    document.body.style.overflow = ''
  }
})

const form = ref<WalletCreate>({
  name: '',
  wallet_type: 'cash' as WalletType,
  balance: 0,
  currency: 'CNY',
})

const transferForm = ref({
  from_wallet_id: 0,
  to_wallet_id: 0,
  amount: 0,
  note: '',
})

const walletTypeOptions = [
  { value: 'cash', label: '💵 现金', icon: '💵' },
  { value: 'bank_card', label: '🏦 银行卡', icon: '🏦' },
  { value: 'e_wallet', label: '💳 电子钱包', icon: '💳' },
  { value: 'other', label: '💳 其他', icon: '💳' },
]

onMounted(() => {
  walletStore.fetchWallets()
})

function openAddModal() {
  editingWallet.value = null
  form.value = { name: '', wallet_type: WalletType.CASH, balance: 0, currency: 'CNY' }
  showModal.value = true
}

function openEditModal(wallet: any) {
  editingWallet.value = wallet
  form.value = {
    name: wallet.name,
    wallet_type: wallet.wallet_type,
    balance: wallet.balance,
    currency: wallet.currency,
  }
  showModal.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (editingWallet.value && 'id' in editingWallet.value) {
      await walletStore.updateWallet((editingWallet.value as any).id, form.value)
    } else {
      await walletStore.createWallet(form.value)
    }
    showModal.value = false
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败，请重试')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: number) {
  if (confirm('确定要删除这个账户吗？')) {
    await walletStore.deleteWallet(id)
  }
}

function openTransferModal() {
  transferForm.value = {
    from_wallet_id: walletStore.wallets[0]?.id || 0,
    to_wallet_id: walletStore.wallets[1]?.id || 0,
    amount: 0,
    note: '',
  }
  showTransferModal.value = true
}

async function handleTransfer() {
  await walletStore.transfer(transferForm.value)
  showTransferModal.value = false
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(amount)
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <h1 class="text-4xl font-medium text-gray-900 tracking-tight" style="letter-spacing: -0.4px;">💼 账户管理</h1>
      <div class="flex gap-3">
        <button
          @click="openTransferModal"
          class="px-6 py-3 bg-white text-gray-900 rounded-full font-medium hover:bg-gray-100 transition-colors border border-gray-200 text-base"
        >
          转账
        </button>
        <button
          @click="openAddModal"
          class="px-6 py-3 bg-gray-900 text-white rounded-full font-medium hover:opacity-85 transition-opacity text-base"
        >
          + 添加账户
        </button>
      </div>
    </div>

    <!-- Total Balance -->
    <div class="bg-gray-900 rounded-2xl p-8 text-white border border-gray-200">
      <p class="text-gray-400 mb-2 text-sm font-medium" style="letter-spacing: 0.16px;">总资产</p>
      <p class="text-5xl font-medium tracking-tight" style="letter-spacing: -0.32px;">{{ formatCurrency(walletStore.totalBalance) }}</p>
    </div>

    <!-- Wallet List -->
    <div v-if="walletStore.wallets.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div
        v-for="wallet in walletStore.wallets"
        :key="wallet.id"
        class="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow"
      >
        <div class="flex justify-between items-start mb-5">
          <div class="flex items-center gap-4">
            <span class="text-4xl">
              {{ wallet.wallet_type === 'cash' ? '💵' : wallet.wallet_type === 'bank_card' ? '🏦' : wallet.wallet_type === 'e_wallet' ? '💳' : '💳' }}
            </span>
            <div>
              <p class="text-xl font-medium text-gray-900" style="letter-spacing: 0.24px;">{{ wallet.name }}</p>
              <p class="text-sm text-gray-500 mt-1" style="letter-spacing: 0.16px;">{{ walletTypeOptions.find(t => t.value === wallet.wallet_type)?.label }}</p>
            </div>
          </div>
          <div class="flex gap-2">
            <button @click="openEditModal(wallet)" class="p-2 hover:bg-gray-100 rounded-full transition-colors">✏️</button>
            <button @click="handleDelete(wallet.id)" class="p-2 hover:bg-red-50 rounded-full transition-colors">🗑️</button>
          </div>
        </div>
        <p :class="['text-3xl font-medium tracking-tight', wallet.balance >= 0 ? 'text-emerald-600' : 'text-red-500']" style="letter-spacing: -0.32px;">
          {{ formatCurrency(wallet.balance) }}
        </p>
      </div>
    </div>

    <div v-else class="text-center py-16 text-gray-500 bg-white rounded-2xl border border-gray-100">
      <p class="text-lg mb-4" style="letter-spacing: 0.24px;">还没有账户，添加一个开始记账吧</p>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl p-8 w-full max-w-md border border-gray-100 max-h-[90vh] overflow-hidden flex flex-col">
        <h2 class="text-2xl font-medium text-gray-900 mb-6 flex-shrink-0" style="letter-spacing: -0.32px;">{{ editingWallet ? '编辑账户' : '添加账户' }}</h2>
        <form @submit.prevent="handleSubmit" class="space-y-5 flex-1 overflow-y-auto pr-1">
          <div>
            <label for="wallet-name" class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">账户名称</label>
            <input id="wallet-name" v-model="form.name" type="text" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">账户类型</label>
            <select v-model="form.wallet_type" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all">
              <option v-for="opt in walletTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">初始余额</label>
            <input v-model.number="form.balance" type="number" step="0.01" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all" />
          </div>
          <div class="flex gap-3 pt-3 flex-shrink-0">
            <button type="button" @click="showModal = false" class="flex-1 py-3 border border-gray-200 rounded-full font-medium hover:bg-gray-100 transition-colors text-base">取消</button>
            <button type="submit" :disabled="submitting" class="flex-1 py-3 bg-gray-900 text-white rounded-full font-medium hover:opacity-85 transition-opacity disabled:opacity-50 text-base">{{ submitting ? '保存中...' : '保存' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Transfer Modal -->
    <div v-if="showTransferModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl p-8 w-full max-w-md border border-gray-100 max-h-[90vh] overflow-hidden flex flex-col">
        <h2 class="text-2xl font-medium text-gray-900 mb-6 flex-shrink-0" style="letter-spacing: -0.32px;">💸 转账</h2>
        <form @submit.prevent="handleTransfer" class="space-y-5 flex-1 overflow-y-auto pr-1">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">从</label>
            <select v-model="transferForm.from_wallet_id" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">到</label>
            <select v-model="transferForm.to_wallet_id" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">金额</label>
            <input v-model.number="transferForm.amount" type="number" step="0.01" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">备注</label>
            <input v-model="transferForm.note" type="text" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all" />
          </div>
          <div class="flex gap-3 pt-3 flex-shrink-0">
            <button type="button" @click="showTransferModal = false" class="flex-1 py-3 border border-gray-200 rounded-full font-medium hover:bg-gray-100 transition-colors text-base">取消</button>
            <button type="submit" class="flex-1 py-3 bg-gray-900 text-white rounded-full font-medium hover:opacity-85 transition-opacity text-base">转账</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>