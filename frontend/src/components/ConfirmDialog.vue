<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" @click.self="onCancel">
    <div class="bg-white rounded-2xl p-6 w-full max-w-sm mx-4 shadow-xl">
      <div class="mb-4">
        <h3 v-if="options.title" class="text-lg font-semibold text-gray-900">{{ options.title }}</h3>
        <p class="text-gray-600 mt-2">{{ options.message }}</p>
      </div>
      
      <div class="flex gap-3">
        <button
          type="button"
          @click="onCancel"
          class="flex-1 py-3 border border-gray-200 rounded-full text-gray-700 hover:bg-gray-50 transition-colors"
        >
          {{ options.cancelText || '取消' }}
        </button>
        <button
          type="button"
          @click="onConfirm"
          class="flex-1 py-3 bg-red-600 text-white rounded-full hover:bg-red-700 transition-colors"
        >
          {{ options.confirmText || '确认' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useConfirmStore } from '@/stores/confirm'

const confirmStore = useConfirmStore()
const { show, options } = storeToRefs(confirmStore)

function onConfirm() {
  confirmStore.onConfirm()
}

function onCancel() {
  confirmStore.onCancel()
}
</script>