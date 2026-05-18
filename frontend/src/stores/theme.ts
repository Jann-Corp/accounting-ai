import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(false)

  // 初始化：读取 localStorage 并同步 HTML class
  const init = () => {
    const stored = localStorage.getItem('theme')
    if (stored === 'dark') {
      isDark.value = true
      document.documentElement.classList.add('dark')
    } else {
      isDark.value = false
      document.documentElement.classList.remove('dark')
    }
  }

  const toggle = () => {
    isDark.value = !isDark.value
  }

  watch(isDark, (val) => {
    if (val) {
      localStorage.setItem('theme', 'dark')
      document.documentElement.classList.add('dark')
    } else {
      localStorage.setItem('theme', 'light')
      document.documentElement.classList.remove('dark')
    }
  })

  return { isDark, init, toggle }
})
