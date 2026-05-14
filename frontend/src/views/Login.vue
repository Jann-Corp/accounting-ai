<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const isLogin = ref(true)
const form = ref({
  username: '',
  email: '',
  password: '',
})
const error = ref('')

const formValid = computed(() => {
  if (isLogin.value) {
    return form.value.username && form.value.password
  }
  return form.value.username && form.value.email && form.value.password
})

async function handleSubmit() {
  error.value = ''
  try {
    if (isLogin.value) {
      await authStore.login({
        username: form.value.username,
        password: form.value.password,
      })
    } else {
      await authStore.register({
        username: form.value.username,
        email: form.value.email,
        password: form.value.password,
      })
    }
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '操作失败，请重试'
  }
}

function toggleMode() {
  isLogin.value = !isLogin.value
  error.value = ''
}

function toggleTheme() {
  themeStore.toggle()
}
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center p-4"
    style="background: var(--bg-primary);"
  >
    <!-- Theme Toggle Floating -->
    <button
      @click="toggleTheme"
      class="absolute top-6 right-6 p-3 rounded-xl transition"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-md);"
      :title="themeStore.isDark ? '切换到浅色模式' : '切换到深色模式'"
    >
      <span class="text-2xl">{{ themeStore.isDark ? '☀️' : '🌙' }}</span>
    </button>

    <div
      class="w-full max-w-md rounded-2xl p-8"
      style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);"
    >
      <!-- Logo -->
      <div class="text-center mb-8">
        <div
          class="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
          style="background: var(--gradient-gold); box-shadow: var(--shadow-gold);"
        >
          <span class="text-3xl">💰</span>
        </div>
        <h1 class="text-3xl font-bold text-gradient-gold mb-1">AI记账</h1>
        <p style="color: var(--text-muted);">
          {{ isLogin ? '登录您的账户' : '创建新账户' }}
        </p>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-4 p-3 rounded-xl text-sm"
        style="background: rgba(239, 68, 68, 0.1); color: var(--expense-color); border: 1px solid rgba(239, 68, 68, 0.2);"
      >
        {{ error }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Username -->
        <div>
          <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">用户名</label>
          <input
            v-model="form.username"
            type="text"
            class="input-gold"
            placeholder="请输入用户名"
          />
        </div>

        <!-- Email (register only) -->
        <div v-if="!isLogin">
          <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">邮箱</label>
          <input
            v-model="form.email"
            type="email"
            class="input-gold"
            placeholder="请输入邮箱"
          />
        </div>

        <!-- Password -->
        <div>
          <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">密码</label>
          <input
            v-model="form.password"
            type="password"
            class="input-gold"
            placeholder="请输入密码"
          />
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="!formValid || authStore.loading"
          class="btn-gold w-full mt-2"
        >
          {{ authStore.loading ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>

      <!-- Toggle Mode -->
      <p class="text-center mt-6 text-sm" style="color: var(--text-muted);">
        {{ isLogin ? '还没有账户？' : '已有账户？' }}
        <button
          @click="toggleMode"
          class="font-semibold ml-1 transition"
          style="color: var(--accent-gold);"
        >
          {{ isLogin ? '立即注册' : '去登录' }}
        </button>
      </p>
    </div>
  </div>
</template>
