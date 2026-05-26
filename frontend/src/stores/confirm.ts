import { ref } from 'vue'
import { defineStore } from 'pinia'

export interface ConfirmDialogOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
}

export const useConfirmStore = defineStore('confirm', () => {
  const show = ref(false)
  const options = ref<ConfirmDialogOptions>({ message: '' })
  const resolvePromise = ref<((value: boolean) => void) | null>(null)

  function confirm(opts: ConfirmDialogOptions): Promise<boolean> {
    show.value = true
    options.value = opts
    
    return new Promise<boolean>((resolve) => {
      resolvePromise.value = resolve
    })
  }

  function onConfirm() {
    if (resolvePromise.value) {
      resolvePromise.value(true)
      resolvePromise.value = null
    }
    show.value = false
  }

  function onCancel() {
    if (resolvePromise.value) {
      resolvePromise.value(false)
      resolvePromise.value = null
    }
    show.value = false
  }

  return {
    show,
    options,
    confirm,
    onConfirm,
    onCancel,
  }
})