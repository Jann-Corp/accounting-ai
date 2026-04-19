import { defineStore } from 'pinia'
import { ref } from 'vue'
import { categoryApi } from '@/api'
import type { Category, CategoryCreate, CategoryType } from '@/types'

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>([])
  const loading = ref(false)

  async function fetchCategories(categoryType?: CategoryType) {
    loading.value = true
    try {
      const res = await categoryApi.list(categoryType)
      categories.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createCategory(data: CategoryCreate) {
    const res = await categoryApi.create(data)
    categories.value.push(res.data)
    return res.data
  }

  async function updateCategory(id: number, data: Partial<CategoryCreate>) {
    const res = await categoryApi.update(id, data)
    const idx = categories.value.findIndex(c => c.id === id)
    if (idx !== -1) categories.value[idx] = res.data
    return res.data
  }

  async function deleteCategory(id: number) {
    await categoryApi.delete(id)
    categories.value = categories.value.filter(c => c.id !== id)
  }

  return {
    categories,
    loading,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
  }
})
