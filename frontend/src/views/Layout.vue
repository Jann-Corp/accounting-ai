<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useWalletStore } from '@/stores/wallet'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const walletStore = useWalletStore()

const showSidebar = ref(false)

onMounted(async () => {
  if (authStore.user) {
    await walletStore.fetchWallets()
  }
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function confirmLogout() {
  if (confirm('确定要退出登录吗？')) {
    handleLogout()
  }
}

const navItems = [
  { path: '/', label: '首页', icon: '📊' },
  { path: '/records', label: '记账', icon: '📝' },
  { path: '/upload', label: 'AI识别', icon: '🤖' },
  { path: '/wallets', label: '账户', icon: '💼' },
  { path: '/categories', label: '分类', icon: '🏷️' },
  { path: '/stats', label: '统计', icon: '📈' },
  { path: '/api-keys', label: 'API Keys', icon: '🔑' },
  { path: '/ai-records', label: 'AI 记录', icon: '🤖' },
]

const currentPath = ref(route.path)

// Keep currentPath in sync with route changes
watch(() => route.path, (p) => { currentPath.value = p })
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Mobile Header -->
    <header class="sticky top-0 z-50 bg-white shadow-sm lg:hidden">
      <div class="flex items-center justify-between p-4">
        <button @click="showSidebar = !showSidebar" class="p-2 rounded-lg hover:bg-gray-100">
          <span class="text-xl">☰</span>
        </button>
        <h1 class="font-bold text-indigo-600">💰 AI记账</h1>
        <button @click="confirmLogout" class="p-2 rounded-lg hover:bg-gray-100">
          <span class="text-xl">🚪</span>
        </button>
      </div>
    </header>

    <!-- Sidebar -->
    <aside
      :class="['fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform lg:translate-x-0 lg:static', showSidebar ? 'translate-x-0' : '-translate-x-full']"
    >
      <div class="p-6 border-b">
        <h1 class="text-2xl font-bold text-indigo-600">💰 AI记账</h1>
        <p class="text-sm text-gray-500 mt-1">{{ authStore.user?.username }}</p>
      </div>

      <nav class="p-4 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          @click="showSidebar = false"
          :class="['flex items-center gap-3 px-4 py-3 rounded-lg transition', currentPath === item.path ? 'bg-indigo-50 text-indigo-600' : 'hover:bg-gray-50']"
        >
          <span class="text-xl">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="absolute bottom-0 left-0 right-0 p-4 border-t bg-white">
        <div class="text-sm text-gray-500 mb-2">总资产</div>
        <div class="text-2xl font-bold text-green-600">
          ¥{{ walletStore.totalBalance.toFixed(2) }}
        </div>
      </div>
    </aside>

    <!-- Mobile overlay -->
    <div
      v-if="showSidebar"
      @click="showSidebar = false"
      class="fixed inset-0 bg-black/50 z-40 lg:hidden"
    />

    <!-- Main Content -->
    <main class="flex-1 p-6 lg:p-8">
      <RouterView />
    </main>
  </div>
</template>
