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

const icons = ['🍜', '🚗', '🛒', '🎮', '💊', '📚', '🏠', '📱', '💰', '💼', '📈', '🎁', '💵', '🏷️', '📦', '✈️', '🎓', '👶', '🐱', '⚽']

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
    <!-- Header -->
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold" style="color: var(--text-primary);">🏷️ 分类管理</h1>
      <button @click="openAddModal" class="btn-gold">
        + 添加分类
      </button>
    </div>

    <!-- Filter Tabs -->
    <div
      class="flex gap-2 p-1.5 rounded-xl"
      style="background: var(--bg-card); border: 1px solid var(--border-color);"
    >
      <button
        v-for="tab in [
          { value: '', label: '全部' },
          { value: CategoryType.EXPENSE, label: '支出' },
          { value: CategoryType.INCOME, label: '收入' },
        ]"
        :key="tab.value"
        @click="filterType = tab.value as any"
        class="flex-1 py-2 rounded-lg text-sm font-medium transition"
        :style="
          filterType === tab.value
            ? 'background: var(--accent-gold); color: #1C1917;'
            : 'color: var(--text-muted);'
        "
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Category Grid -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      <div
        v-for="category in filteredCategories"
        :key="category.id"
        class="rounded-xl p-4 flex items-center justify-between transition"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-sm);"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
            :style="{ background: category.category_type === 'expense' ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)' }"
          >
            {{ category.icon }}
          </div>
          <div>
            <p class="font-medium text-sm" style="color: var(--text-primary);">{{ category.name }}</p>
            <p class="text-xs" style="color: var(--text-muted);">
              {{ category.category_type === 'expense' ? '支出' : '收入' }}
              <span
                v-if="category.is_default"
                class="ml-1 px-1.5 py-0.5 rounded text-xs"
                style="background: var(--accent-gold-light); color: var(--accent-gold);"
              >
                默认
              </span>
            </p>
          </div>
        </div>
        <div v-if="!category.is_default" class="flex gap-1">
          <button
            @click="openEditModal(category)"
            class="p-1.5 rounded-lg transition"
            style="color: var(--text-muted);"
          >
            ✏️
          </button>
          <button
            @click="handleDelete(category.id)"
            class="p-1.5 rounded-lg transition"
            style="color: var(--text-muted);"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="filteredCategories.length === 0"
      class="text-center py-12 rounded-2xl"
      style="background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-muted);"
    >
      还没有分类
    </div>

    <!-- Modal -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay"
      @click.self="showModal = false"
    >
      <div
        class="rounded-2xl p-6 w-full max-w-md"
        style="background: var(--bg-card); border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);"
      >
        <h2 class="text-xl font-bold mb-6" style="color: var(--text-primary);">
          {{ editingCategory ? '✏️ 编辑分类' : '➕ 添加分类' }}
        </h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">分类名称</label>
            <input v-model="form.name" type="text" class="input-gold" placeholder="例如：餐饮" required />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--text-secondary);">类型</label>
            <select v-model="form.category_type" class="input-gold">
              <option value="expense">支出</option>
              <option value="income">收入</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-2" style="color: var(--text-secondary);">图标</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="icon in icons"
                :key="icon"
                type="button"
                @click="form.icon = icon"
                class="text-2xl p-2 rounded-lg border transition"
                :style="
                  form.icon === icon
                    ? 'border-color: var(--accent-gold); background: var(--accent-gold-light);'
                    : 'border-color: var(--border-color);'
                "
              >
                {{ icon }}
              </button>
            </div>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showModal = false" class="flex-1 py-2.5 rounded-xl border" style="border-color: var(--border-color); color: var(--text-secondary);">
              取消
            </button>
            <button type="submit" class="flex-1 btn-gold">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
