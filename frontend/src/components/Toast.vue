<script setup lang="ts">
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()

const typeClasses = {
  success: 'bg-green-500 text-white',
  error: 'bg-red-500 text-white',
  info: 'bg-blue-500 text-white',
  warning: 'bg-yellow-500 text-white'
}

const typeIcons = {
  success: '✓',
  error: '✗',
  info: 'ℹ',
  warning: '⚠'
}
</script>

<template>
  <div class="fixed top-4 right-4 z-50 flex flex-col gap-2">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg min-w-64 max-w-md"
        :class="typeClasses[toast.type]"
      >
        <span class="text-lg">{{ typeIcons[toast.type] }}</span>
        <span class="flex-1 text-sm">{{ toast.message }}</span>
        <button
          @click="toastStore.remove(toast.id)"
          class="text-white/80 hover:text-white text-lg"
        >
          ×
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>