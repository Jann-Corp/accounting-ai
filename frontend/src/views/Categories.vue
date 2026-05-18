<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCategoryStore } from '@/stores/category'
import { CategoryType } from '@/types'
import type { Category, CategoryCreate } from '@/types'

const categoryStore = useCategoryStore()

const showModal = ref(false)
const editingCategory = ref<Category | null>(null)
const filterType = ref<CategoryType | ''>('')

const form = ref<CategoryCreate>({
  name: '',
  category_type: 'expense' as CategoryType,
  icon: '📦',
})

const icons = ['🍜', '🚗', '🛒', '🎮', '💊', '📚', '🏠', '📱', '💰', '💼', '📈', '🎁', '💵', '🏷️', '📦']

const filteredCategories = computed(() => {
  if (filterType.value) {
    return categoryStore.categories.filter(c => c.category_type === filterType.value)
  }
  return categoryStore.categories
})

const expenseCategories = computed(() =>
  categoryStore.categories.filter(c => c.category_type === CategoryType.EXPENSE)
)
const incomeCategories = computed(() =>
  categoryStore.categories.filter(c => c.category_type === CategoryType.INCOME)
)

onMounted(() => {
  categoryStore.fetchCategories()
})

function openAddModal() {
  editingCategory.value = null
  form.value = { name: '', category_type: CategoryType.EXPENSE, icon: '📦' }
  showModal.value = true
}

function openEditModal(category: Category) {
  editingCategory.value = category
  form.value = {
    name: category.name,
    category_type: category.category_type,
    icon: category.icon,
  }
  showModal.value = true
}

async function handleSubmit() {
  if (editingCategory.value) {
    await categoryStore.updateCategory(editingCategory.value.id, form.value)
  } else {
    await categoryStore.createCategory(form.value)
  }
  showModal.value = false
}

async function handleDelete(id: number) {
  if (confirm('确定要删除这个分类吗？')) {
    await categoryStore.deleteCategory(id)
  }
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex justify-between items-center">
      <h1 class="text-5xl font-semibold text-gray-900 tracking-tight">分类管理</h1>
      <button
        @click="openAddModal"
        class="bg-gray-900 text-white px-8 py-3.5 rounded-full hover:opacity-85 font-medium text-sm"
      >
        添加分类
      </button>
    </div>

    <!-- Filter -->
    <div class="flex gap-2 border border-gray-100 bg-white rounded-2xl p-2">
      <button
        @click="filterType = ''"
        :class="['px-6 py-2.5 rounded-full text-sm transition-colors', !filterType ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-100']"
      >
        全部
      </button>
      <button
        @click="filterType = CategoryType.EXPENSE"
        :class="['px-6 py-2.5 rounded-full text-sm transition-colors', filterType === CategoryType.EXPENSE ? 'bg-red-500 text-white' : 'text-gray-600 hover:bg-gray-100']"
      >
        支出
      </button>
      <button
        @click="filterType = CategoryType.INCOME"
        :class="['px-6 py-2.5 rounded-full text-sm transition-colors', filterType === CategoryType.INCOME ? 'bg-emerald-600 text-white' : 'text-gray-600 hover:bg-gray-100']"
      >
        收入
      </button>
    </div>

    <!-- Category List -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div
        v-for="category in filteredCategories"
        :key="category.id"
        class="border border-gray-100 bg-white rounded-2xl p-5 flex items-center justify-between hover:border-gray-200 transition-colors"
      >
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center text-2xl">
            {{ category.icon }}
          </div>
          <div>
            <p class="font-semibold text-gray-900 text-sm">{{ category.name }}</p>
            <p class="text-xs text-gray-500 mt-1">
              {{ category.category_type === 'expense' ? '支出' : '收入' }}
              <span v-if="category.is_default" class="text-gray-400 ml-1">默认</span>
            </p>
          </div>
        </div>
        <div v-if="!category.is_default" class="flex gap-1">
          <button @click="openEditModal(category)" class="p-2 text-gray-400 hover:text-gray-900 transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button @click="handleDelete(category.id)" class="p-2 text-gray-400 hover:text-red-500 transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-if="filteredCategories.length === 0" class="text-center py-16 text-gray-400 border border-gray-100 bg-white rounded-2xl">
      还没有分类
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div class="border border-gray-100 bg-white rounded-2xl p-8 w-full max-w-md">
        <h2 class="text-2xl font-semibold text-gray-900 mb-6 tracking-tight">{{ editingCategory ? '编辑分类' : '添加分类' }}</h2>
        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">分类名称</label>
            <input v-model="form.name" type="text" class="w-full border border-gray-100 rounded-full px-4 py-3 bg-white text-gray-900" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">类型</label>
            <select v-model="form.category_type" class="w-full border border-gray-100 rounded-full px-4 py-3 bg-white text-gray-600">
              <option value="expense">支出</option>
              <option value="income">收入</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-2">图标</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="icon in icons"
                :key="icon"
                type="button"
                @click="form.icon = icon"
                :class="['text-2xl p-3 rounded-2xl border-2 transition-all', form.icon === icon ? 'border-gray-900 bg-gray-50' : 'border-gray-100 hover:border-gray-200']"
              >
                {{ icon }}
              </button>
            </div>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-3 border border-gray-200 rounded-full text-gray-700 hover:bg-gray-50 transition-colors">取消</button>
            <button type="submit" class="flex-1 py-3 bg-gray-900 text-white rounded-full hover:opacity-85 transition-opacity">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
