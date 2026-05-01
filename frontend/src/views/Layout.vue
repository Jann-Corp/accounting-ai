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
  { path: '/records', label: '记账记录', icon: '📝' },
  { path: '/upload', label: '上传小票', icon: '🧾' },
  { path: '/wallets', label: '账户', icon: '💼' },
  { path: '/categories', label: '分类', icon: '🏷️' },
  { path: '/stats', label: '统计', icon: '📈' },
  { path: '/api-keys', label: 'API Keys', icon: '🔑' },
  { path: '/ai-records', label: 'AI 记录', icon: '🤖', hasBadge: true },
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
      :class="['fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform lg:translate-x-0 lg:static flex flex-col', showSidebar ? 'translate-x-0' : '-translate-x-full']"
    >
      <div class="p-6 border-b flex-shrink-0">
        <h1 class="text-2xl font-bold text-indigo-600">💰 AI记账</h1>
        <p class="text-sm text-gray-500 mt-1">{{ authStore.user?.username }}</p>
      </div>

      <nav class="p-4 space-y-1 flex-1 overflow-y-auto">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          @click="showSidebar = false"
          :class="['flex items-center gap-3 px-4 py-3 rounded-lg transition', currentPath === item.path ? 'bg-indigo-50 text-indigo-600' : 'hover:bg-gray-50']"
        >
          <span class="text-xl relative">
            {{ item.icon }}
            <!-- 动态小红点 -->
            <span
              v-if="item.hasBadge && aiRecordStore.showBadge"
              class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse border-2 border-white"
            />
          </span>
          <span class="flex-1">{{ item.label }}</span>
          <!-- 数字提示 -->
          <span
            v-if="item.hasBadge && aiRecordStore.pendingCount > 0"
            class="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded-full"
          >
            {{ aiRecordStore.pendingCount }}
          </span>
        </router-link>
      </nav>

      <div class="p-4 border-t bg-white flex-shrink-0">
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

    <!-- Floating Action Button -->
    <button
      @click="showRecordModal = true"
      class="fixed bottom-6 right-6 w-14 h-14 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 flex items-center justify-center text-2xl lg:bottom-8 lg:right-8 z-30"
    >
      ✏️
    </button>

    <!-- Record Modal -->
    <RecordModal :show="showRecordModal" @close="showRecordModal = false" />
  </div>
</template>
