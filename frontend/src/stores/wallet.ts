import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { walletApi } from '@/api'
import type { Wallet, WalletCreate, TransferRequest } from '@/types'

export const useWalletStore = defineStore('wallet', () => {
  const wallets = ref<Wallet[]>([])
  const loading = ref(false)

  const totalBalance = computed(() =>
    wallets.value.reduce((sum, w) => sum + w.balance, 0)
  )

  async function fetchWallets() {
    loading.value = true
    try {
      const res = await walletApi.list()
      wallets.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createWallet(data: WalletCreate) {
    const res = await walletApi.create(data)
    wallets.value.push(res.data)
    return res.data
  }

  async function updateWallet(id: number, data: Partial<WalletCreate>) {
    const res = await walletApi.update(id, data)
    const idx = wallets.value.findIndex(w => w.id === id)
    if (idx !== -1) wallets.value[idx] = res.data
    return res.data
  }

  async function deleteWallet(id: number) {
    await walletApi.delete(id)
    wallets.value = wallets.value.filter(w => w.id !== id)
  }

  async function transfer(data: TransferRequest) {
    await walletApi.transfer(data)
    await fetchWallets()
  }

  return {
    wallets,
    loading,
    totalBalance,
    fetchWallets,
    createWallet,
    updateWallet,
    deleteWallet,
    transfer,
  }
})
