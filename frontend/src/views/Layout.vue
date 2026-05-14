<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useWalletStore } from '@/stores/wallet'
import { useAIRecordStore } from '@/stores/aiRecord'
import { useThemeStore } from '@/stores/theme'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const walletStore = useWalletStore()
const aiRecordStore = useAIRecordStore()
const themeStore = useThemeStore()

const showSidebar = ref(false)

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

function toggleTheme() {
  themeStore.toggle()
}

const navItems = [
  { path: '/', label: '首页', icon: '📊' },
  { path: '/records', label: '记账', icon: '📝' },
  { path: '/upload', label: 'AI 识别', icon: '🤖' },
  { path: '/wallets', label: '账户', icon: '💼' },
  { path: '/categories', label: '分类', icon: '🏷️' },
  { path: '/stats', label: '统计', icon: '📈' },
  { path: '/api-keys', label: 'API Keys', icon: '🔑' },
  { path: '/ai-records', label: 'AI 记录', icon: '🤖', hasBadge: true },
  { path: '/settings', label: '设置', icon: '⚙️' },
]

const currentPath = ref(route.path)
let isFirstRoute = true

watch(() => route.path, (p) => {
  currentPath.value = p
  if (p === '/ai-records') {
    aiRecordStore.markAsViewed()
  }
  if (!isFirstRoute && authStore.user) {
    aiRecordStore.fetchPendingRecords()
  }
  isFirstRoute = false
})
</script>

<template>
  <div class="min-h-screen" style="background-color: var(--bg-primary); color: var(--text-primary);">
    <!-- Mobile Header -->
    <header
      class="sticky top-0 z-50 lg:hidden border-b"
      style="background-color: var(--bg-card); border-color: var(--border-color);"
    >
      <div class="flex items-center justify-between p-4">
        <button
          @click="showSidebar = !showSidebar"
          class="p-2 rounded-lg"
          style="hover:background-color: var(--bg-hover);"
        >
          <span class="text-xl">☰</span>
        </button>
        <h1 class="font-bold text-gold">💰 AI记账</h1>
        <div class="flex items-center gap-2">
          <!-- Theme Toggle Mobile -->
          <button
            @click="toggleTheme"
            class="p-2 rounded-lg"
            style="hover:background-color: var(--bg-hover);"
          >
            <span class="text-xl">{{ themeStore.isDark ? '🌙' : '☀️' }}</span>
          </button>
          <button
            @click="confirmLogout"
            class="p-2 rounded-lg"
            style="hover:background-color: var(--bg-hover);"
          >
            <span class="text-xl">🚪</span>
          </button>
        </div>
      </div>
    </header>

    <!-- Sidebar -->
    <aside
      :class="['fixed inset-y-0 left-0 z-50 w-64 flex flex-col transform transition-transform lg:translate-x-0 lg:static', showSidebar ? 'translate-x-0' : '-translate-x-full']"
      style="background-color: var(--bg-secondary); border-right: 1px solid var(--border-color);"
    >
      <!-- Logo -->
      <div class="p-6 border-b flex-shrink-0" style="border-color: var(--border-color);">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gradient-gold">💰 AI记账</h1>
            <p class="text-sm mt-1" style="color: var(--text-secondary);">{{ authStore.user?.username }}</p>
          </div>
          <!-- Desktop Theme Toggle -->
          <button
            @click="toggleTheme"
            class="p-2 rounded-lg transition"
            style="hover:background-color: var(--bg-hover);"
            title="切换主题"
          >
            <span class="text-xl">{{ themeStore.isDark ? '🌙' : '☀️' }}</span>
          </button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="p-4 space-y-1 flex-1 overflow-y-auto">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          @click="showSidebar = false"
          :class="['flex items-center gap-3 px-4 py-3 rounded-xl transition', currentPath === item.path ? 'text-gold font-semibold' : '']"
          :style="currentPath === item.path
            ? 'background-color: var(--accent-gold-light); color: var(--accent-gold);'
            : 'color: var(--text-secondary); hover:background-color: var(--bg-hover);'"
        >
          <span class="text-xl relative">
            {{ item.icon }}
            <span
              v-if="item.hasBadge && aiRecordStore.showBadge"
              class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse border-2 border-white"
            />
          </span>
          <span class="flex-1">{{ item.label }}</span>
          <span
            v-if="item.hasBadge && aiRecordStore.pendingCount > 0"
            class="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded-full"
          >
            {{ aiRecordStore.pendingCount }}
          </span>
        </router-link>
      </nav>

      <!-- Balance Footer -->
      <div class="p-4 border-t flex-shrink-0" style="border-color: var(--border-color); background-color: var(--bg-card);">
        <div class="text-sm mb-1" style="color: var(--text-muted);">总资产</div>
        <div class="text-2xl font-bold text-gold">
          ¥{{ walletStore.totalBalance.toFixed(2) }}
        </div>
      </div>
    </aside>

    <!-- Mobile overlay -->
    <div
      v-if="showSidebar"
      @click="showSidebar = false"
      class="fixed inset-0 z-40 lg:hidden"
      style="background-color: var(--bg-primary); opacity: 0.7;"
    />

    <!-- Main Content -->
    <main class="flex-1 p-6 lg:p-8">
      <RouterView />
    </main>
  </div>
</template>
