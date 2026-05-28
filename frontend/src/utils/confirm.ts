import { useConfirmStore } from '@/stores/confirm'

export async function showConfirm(
  message: string,
  title?: string,
  confirmText?: string,
  cancelText?: string
): Promise<boolean> {
  const confirmStore = useConfirmStore()
  
  return await confirmStore.confirm({
    message,
    title,
    confirmText,
    cancelText,
  })
}

// 常用的确认函数
export async function confirmDelete(message: string = '确定要删除吗？'): Promise<boolean> {
  return await showConfirm(message, '确认删除', '删除', '取消')
}

export async function confirmLogout(): Promise<boolean> {
  return await showConfirm('确定要退出登录吗？', '确认退出', '退出', '取消')
}