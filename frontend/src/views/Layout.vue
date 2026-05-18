<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useWalletStore } from '@/stores/wallet'
import { useAIRecordStore } from '@/stores/aiRecord'
import RecordModal from '@/components/RecordModal.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const walletStore = useWalletStore()
const aiRecordStore = useAIRecordStore()

const showSidebar = ref(false)
const showRecordModal = ref(false)

onMounted(async () => {
  if (authStore.user) {
    await Promise.all([
      walletStore.fetchWallets(),
      aiRecordStore.fetchPendingRecords(),
    ])
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
  { path: '/records', label: '流水', icon: '📝' },
  { path: '/wallets', label: '账户', icon: '💼' },
  { path: '/categories', label: '分类', icon: '🏷️' },
  { path: '/stats', label: '统计', icon: '📈' },
  { path: '/api-keys', label: 'API Keys', icon: '🔑' },
  { path: '/ai-records', label: 'AI记账记录', icon: '🤖', hasBadge: true },
  { path: '/settings', label: '设置', icon: '⚙️' },
]

const currentPath = ref(route.path)
let isFirstRoute = true

// Keep currentPath in sync with route changes
watch(() => route.path, (p) => {
  currentPath.value = p
  // 如果用户进入 AI 记录页面，标记为已查看
  if (p === '/ai-records') {
    aiRecordStore.markAsViewed()
  }
  // 每次路由变化时重新获取待确认记录（除了第一次）
  if (!isFirstRoute && authStore.user) {
    aiRecordStore.fetchPendingRecords()
  }
  isFirstRoute = false
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Mobile Header -->
    <header class="sticky top-0 z-50 bg-white border-b border-gray-100 lg:hidden">
      <div class="flex items-center justify-between px-4 py-4">
        <button @click="showSidebar = !showSidebar" class="p-3 rounded-full hover:bg-gray-100 transition-colors">
          <span class="text-xl">☰</span>
        </button>
        <h1 class="text-xl font-medium text-gray-900" style="letter-spacing: -0.32px;">💰 AI记账</h1>
        <button @click="confirmLogout" class="p-3 rounded-full hover:bg-gray-100 transition-colors">
          <span class="text-xl">🚪</span>
        </button>
      </div>
    </header>

    <!-- Sidebar -->
    <aside
      :class="['fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-gray-100 transform transition-transform lg:translate-x-0 lg:static flex flex-col', showSidebar ? 'translate-x-0' : '-translate-x-full']"
    >
      <div class="p-8 border-b border-gray-100 flex-shrink-0">
        <h1 class="text-3xl font-medium text-gray-900" style="letter-spacing: -0.4px;">💰 AI记账</h1>
        <p class="text-sm text-gray-500 mt-2" style="letter-spacing: 0.16px;">{{ authStore.user?.username }}</p>
      </div>

      <nav class="p-6 space-y-2 flex-1 overflow-y-auto">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          @click="showSidebar = false"
          :class="['flex items-center gap-4 px-5 py-3 rounded-full transition', currentPath === item.path ? 'bg-gray-900 text-white' : 'text-gray-700 hover:bg-gray-100']"
        >
          <span class="text-xl relative">
            {{ item.icon }}
            <span
              v-if="item.hasBadge && aiRecordStore.showBadge"
              class="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 rounded-full animate-pulse border-2 border-white"
            />
          </span>
          <span class="flex-1 text-base font-medium" style="letter-spacing: 0.24px;">{{ item.label }}</span>
          <span
            v-if="item.hasBadge && aiRecordStore.pendingCount > 0"
            class="text-xs bg-red-500 text-white px-2.5 py-1 rounded-full font-medium"
          >
            {{ aiRecordStore.pendingCount }}
          </span>
        </router-link>
      </nav>

      <div class="p-6 border-t border-gray-100 bg-gray-50 flex-shrink-0">
        <div class="text-sm text-gray-500 font-medium mb-1" style="letter-spacing: 0.16px;">总资产</div>
        <div class="text-3xl font-medium text-gray-900" style="letter-spacing: -0.32px;">
          ¥{{ walletStore.totalBalance.toFixed(2) }}
        </div>
      </div>
    </aside>

    <!-- Mobile overlay -->
    <div
      v-if="showSidebar"
      @click="showSidebar = false"
      class="fixed inset-0 bg-black/40 z-40 lg:hidden"
    />

    <!-- Main Content -->
    <main class="flex-1 p-6 sm:p-8 lg:p-10">
      <RouterView />
    </main>

    <!-- Floating Action Button -->
    <button
      @click="showRecordModal = true"
      class="fixed bottom-6 right-6 sm:bottom-8 sm:right-8 w-16 h-16 bg-gray-900 text-white rounded-full shadow-lg hover:opacity-85 transition-opacity flex items-center justify-center text-2xl z-30"
    >
      ✏️
    </button>

    <!-- Record Modal -->
    <RecordModal :show="showRecordModal" @close="showRecordModal = false" />
  </div>
</template>