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
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">🏷️ 分类管理</h1>
      <button
        @click="openAddModal"
        class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
      >
        + 添加分类
      </button>
    </div>

    <!-- Filter -->
    <div class="flex gap-4 bg-white p-4 rounded-lg">
      <button
        @click="filterType = ''"
        :class="['px-4 py-2 rounded-lg', !filterType ? 'bg-indigo-100 text-indigo-600' : 'hover:bg-gray-100']"
      >
        全部
      </button>
      <button
        @click="filterType = CategoryType.EXPENSE"
        :class="['px-4 py-2 rounded-lg', filterType === CategoryType.EXPENSE ? 'bg-red-100 text-red-600' : 'hover:bg-gray-100']"
      >
        支出
      </button>
      <button
        @click="filterType = CategoryType.INCOME"
        :class="['px-4 py-2 rounded-lg', filterType === CategoryType.INCOME ? 'bg-green-100 text-green-600' : 'hover:bg-gray-100']"
      >
        收入
      </button>
    </div>

    <!-- Category List -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div
        v-for="category in filteredCategories"
        :key="category.id"
        class="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between"
      >
        <div class="flex items-center gap-3">
          <span class="text-2xl">{{ category.icon }}</span>
          <div>
            <p class="font-medium">{{ category.name }}</p>
            <p class="text-xs text-gray-500">
              {{ category.category_type === 'expense' ? '支出' : '收入' }}
              <span v-if="category.is_default" class="text-indigo-500 ml-1">默认</span>
            </p>
          </div>
        </div>
        <div v-if="!category.is_default" class="flex gap-1">
          <button @click="openEditModal(category)" class="p-2 hover:bg-gray-100 rounded-lg">✏️</button>
          <button @click="handleDelete(category.id)" class="p-2 hover:bg-red-50 rounded-lg">🗑️</button>
        </div>
      </div>
    </div>

    <div v-if="filteredCategories.length === 0" class="text-center py-12 text-gray-500 bg-white rounded-2xl">
      还没有分类
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">{{ editingCategory ? '编辑分类' : '添加分类' }}</h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">分类名称</label>
            <input v-model="form.name" type="text" class="w-full border rounded-lg px-3 py-2" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">类型</label>
            <select v-model="form.category_type" class="w-full border rounded-lg px-3 py-2">
              <option value="expense">支出</option>
              <option value="income">收入</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">图标</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="icon in icons"
                :key="icon"
                type="button"
                @click="form.icon = icon"
                :class="['text-2xl p-2 rounded-lg border-2', form.icon === icon ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300']"
              >
                {{ icon }}
              </button>
            </div>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-2 border rounded-lg">取消</button>
            <button type="submit" class="flex-1 py-2 bg-indigo-600 text-white rounded-lg">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
