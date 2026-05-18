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
    <!-- Header -->
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold" style="color: var(--text-primary);">💼 账户管理</h1>
      <div class="flex gap-2">
        <button
          @click="openTransferModal"
          class="btn-gold-outline"
          :disabled="walletStore.wallets.length < 2"
        >
          转账
        </button>
        <button @click="openAddModal" class="btn-gold">
          + 添加账户
        </button>
      </div>
    </div>

    <!-- Total Balance Hero -->
    <div
      class="rounded-2xl p-6 text-white relative overflow-hidden"
      style="background: linear-gradient(135deg, #B8922E, #D4A843, #F5D98B); box-shadow: var(--shadow-gold);"
    >
      <div class="absolute top-0 right-0 w-40 h-40 opacity-10 text-9xl">💰</div>
      <p class="text-sm mb-1" style="color: rgba(255,255,255,0.8);">总资产</p>
      <p class="text-4xl font-bold text-amount">{{ formatCurrency(walletStore.totalBalance) }}</p>
    </div>

    <!-- Wallet Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="wallet in walletStore.wallets"
        :key="wallet.id"
        class="rounded-2xl p-5 transition"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
      >
        <div class="flex justify-between items-start mb-4">
          <div class="flex items-center gap-3">
            <div
              class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
              style="background: var(--accent-gold-light);"
            >
              {{ wallet.wallet_type === 'cash' ? '💵' : wallet.wallet_type === 'bank_card' ? '🏦' : '💳' }}
            </div>
            <div>
              <p class="font-bold" style="color: var(--text-primary);">{{ wallet.name }}</p>
              <p class="text-sm" style="color: var(--text-muted);">
                {{ walletTypeOptions.find(t => t.value === wallet.wallet_type)?.label }}
              </p>
            </div>
          </div>
          <div class="flex gap-1">
            <button
              @click="openEditModal(wallet)"
              class="p-2 rounded-lg transition"
              style="color: var(--text-muted); hover:background: var(--bg-hover);"
            >
              ✏️
            </button>
            <button
              @click="handleDelete(wallet.id)"
              class="p-2 rounded-lg transition"
              style="color: var(--text-muted);"
            >
              🗑️
            </button>
          </div>
        </div>
        <p
          class="text-2xl font-bold text-amount"
          :style="{ color: wallet.balance >= 0 ? 'var(--income-color)' : 'var(--expense-color)' }"
        >
          {{ formatCurrency(wallet.balance) }}
        </p>
      </div>
    </div>

    <div
      v-if="walletStore.wallets.length === 0"
      class="text-center py-12 rounded-2xl"
      style="background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-muted);"
    >
      还没有账户，添加一个开始记账吧
    </div>

    <!-- Add/Edit Modal -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay"
      @click.self="showModal = false"
    >
      <div
        class="rounded-2xl p-6 w-full max-w-md"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);"
      >
        <h2 class="text-xl font-bold mb-6" style="color: var(--text-primary);">
          {{ editingWallet ? '✏️ 编辑账户' : '➕ 添加账户' }}
        </h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">账户名称</label>
            <input v-model="form.name" type="text" class="input-gold" placeholder="例如：招商银行卡" required />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">账户类型</label>
            <select v-model="form.wallet_type" class="input-gold">
              <option v-for="opt in walletTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">初始余额</label>
            <input v-model.number="form.balance" type="number" step="0.01" class="input-gold" placeholder="0.00" />
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-2.5 rounded-xl border" style="border-color: var(--border-color); color: var(--text-secondary);">
              取消
            </button>
            <button type="submit" :disabled="submitting" class="flex-1 btn-gold">
              {{ submitting ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Transfer Modal -->
    <div
      v-if="showTransferModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay"
      @click.self="showTransferModal = false"
    >
      <div
        class="rounded-2xl p-6 w-full max-w-md"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);"
      >
        <h2 class="text-xl font-bold mb-6" style="color: var(--text-primary);">💸 转账</h2>
        <form @submit.prevent="handleTransfer" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">从</label>
            <select v-model="transferForm.from_wallet_id" class="input-gold" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div class="flex justify-center">
            <span class="text-2xl" style="color: var(--accent-gold);">↓</span>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">到</label>
            <select v-model="transferForm.to_wallet_id" class="input-gold" required>
              <option v-for="w in walletStore.wallets" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">金额</label>
            <input v-model.number="transferForm.amount" type="number" step="0.01" class="input-gold" placeholder="0.00" required />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">备注</label>
            <input v-model="transferForm.note" type="text" class="input-gold" placeholder="可选" />
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showTransferModal = false" class="flex-1 py-2.5 rounded-xl border" style="border-color: var(--border-color); color: var(--text-secondary);">
              取消
            </button>
            <button type="submit" class="flex-1 btn-gold">转账</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
