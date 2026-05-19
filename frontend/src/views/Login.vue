<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

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
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl p-8 sm:p-12 w-full max-w-md border border-gray-100">
      <div class="text-center mb-10">
        <h1 class="text-4xl font-medium text-gray-900 mb-3" style="letter-spacing: -0.4px;">💰 AI记账</h1>
        <p class="text-gray-500 text-base" style="letter-spacing: 0.24px;">{{ isLogin ? '登录您的账户' : '创建新账户' }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-5">
        <div v-if="error" class="bg-red-50 text-red-600 p-4 rounded-xl text-sm border border-red-100">
          {{ error }}
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">用户名</label>
          <input
            v-model="form.username"
            type="text"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all"
            placeholder="请输入用户名"
          />
        </div>

        <div v-if="!isLogin">
          <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">邮箱</label>
          <input
            v-model="form.email"
            type="email"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all"
            placeholder="请输入邮箱"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2" style="letter-spacing: 0.16px;">密码</label>
          <input
            v-model="form.password"
            type="password"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-transparent transition-all"
            placeholder="请输入密码"
          />
        </div>

        <button
          type="submit"
          :disabled="!formValid || authStore.loading"
          class="w-full bg-gray-900 text-white py-3.5 px-6 rounded-xl font-medium hover:opacity-85 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity text-base"
        >
          {{ authStore.loading ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>

      <p class="text-center mt-8 text-sm text-gray-600" style="letter-spacing: 0.16px;">
        {{ isLogin ? '还没有账户？' : '已有账户？' }}
        <button @click="toggleMode" class="text-blue-500 font-medium hover:underline" style="letter-spacing: 0.16px;">
          {{ isLogin ? '立即注册' : '去登录' }}
        </button>
      </p>
    </div>
  </div>
</template>