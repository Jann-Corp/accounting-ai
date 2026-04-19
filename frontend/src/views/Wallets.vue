<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useWalletStore } from '@/stores/wallet'
import { walletApi } from '@/api'
import { WalletType } from '@/types'
import type { WalletCreate } from '@/types'

const walletStore = useWalletStore()

const showModal = ref(false)
const showTransferModal = ref(false)
const editingWallet = ref<WalletCreate | null>(null)
const submitting = ref(false)

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
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">💼 账户管理</h1>
      <div class="flex gap-2">
        <button
          @click="openTransferModal"
          class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200"
        >
          转账
        </button>
        <button
          @click="openAddModal"
          class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
        >
          + 添加账户
        </button>
      </div>
    </div>

    <!-- Total Balance -->
    <div class="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl p-6 text-white">
      <p class="text-indigo-100 mb-1">总资产</p>
      <p class="text-4xl font-bold">{{ formatCurrency(walletStore.totalBalance) }}</p>
    </div>

    <!-- Wallet List -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="wallet in walletStore.wallets"
        :key="wallet.id"
        class="bg-white rounded-2xl shadow-sm p-6"
      >
        <div class="flex justify-between items-start mb-4">
          <div class="flex items-center gap-3">
            <span class="text-3xl">
              {{ wallet.wallet_type === 'cash' ? '💵' : wallet.wallet_type === 'bank_card' ? '🏦' : wallet.wallet_type === 'e_wallet' ? '💳' : '💳' }}
            </span>
            <div>
              <p class="font-bold text-lg">{{ wallet.name }}</p>
              <p class="text-sm text-gray-500">{{ walletTypeOptions.find(t => t.value === wallet.wallet_type)?.label }}</p>
            </div>
          </div>
          <div class="flex gap-1">
            <button @click="openEditModal(wallet)" class="p-2 hover:bg-gray-100 rounded-lg">✏️</button>
            <button @click="handleDelete(wallet.id)" class="p-2 hover:bg-red-50 rounded-lg">🗑️</button>
          </div>
        </div>
        <p :class="['text-2xl font-bold', wallet.balance >= 0 ? 'text-green-600' : 'text-red-600']">
          {{ formatCurrency(wallet.balance) }}
        </p>
      </div>
    </div>

    <div v-if="walletStore.wallets.length === 0" class="text-center py-12 text-gray-500 bg-white rounded-2xl">
      还没有账户，添加一个开始记账吧
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">{{ editingWallet ? '编辑账户' : '添加账户' }}</h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label for="wallet-name" class="block text-sm font-medium text-gray-700 mb-1">账户名称</label>
            <input id="wallet-name" v-model="form.name" type="text" class="w-full border rounded-lg px-3 py-2" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">账户类型</label>
            <select v-model="form.wallet_type" class="w-full border rounded-lg px-3 py-2">
              <option v-for="opt in walletTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">初始余额</label>
            <input v-model.number="form.balance" type="number" step="0.01" class="w-full border rounded-lg px-3 py-2" />
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-2 border rounded-lg">取消</button>
            <button type="submit" :disabled="submitting" class="flex-1 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50">{{ submitting ? '保存中...' : '保存' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Transfer Modal -->
    <div v-if="showTransferModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">💸 转账</h2>
        <form @submit.prevent="handleTransfer" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">从</label>
            <select v-model="transferForm.from_wallet_id" class="w-full border rounded-lg px-3 py-2" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">到</label>
            <select v-model="transferForm.to_wallet_id" class="w-full border rounded-lg px-3 py-2" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">金额</label>
            <input v-model.number="transferForm.amount" type="number" step="0.01" class="w-full border rounded-lg px-3 py-2" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">备注</label>
            <input v-model="transferForm.note" type="text" class="w-full border rounded-lg px-3 py-2" />
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showTransferModal = false" class="flex-1 py-2 border rounded-lg">取消</button>
            <button type="submit" class="flex-1 py-2 bg-indigo-600 text-white rounded-lg">转账</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
