<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { marked } from 'marked'
import {
  listKbArticles,
  getKbArticle,
  createKbArticle,
  updateKbArticle,
  deleteKbArticle,
  listKbCategories,
  createKbCategory,
  updateKbCategory,
  deleteKbCategory,
} from '../api'
import CategoryTreeNode from '../components/kb/CategoryTreeNode.vue'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const articles = ref<any[]>([])
const categoryTree = ref<any[]>([])
const selectedCategoryId = ref<number | null>(null)
const selectedArticle = ref<any>(null)
const searchText = ref('')
const editMode = ref(false)
const editorVisible = ref(false)
const page = ref(1)
const pageSize = 20
const selectedIds = ref<Set<number>>(new Set())

// 分类管理
const catDialogVisible = ref(false)
const catDialogMode = ref<'create' | 'edit'>('create')
const catForm = ref({ name: '', parent_id: 0 })
const editingCatId = ref<number | null>(null)
const expandedIds = ref<Set<number>>(new Set())

const emptyForm = () => ({
  company_id: companyId,
  title: '',
  content_md: '',
  category_id: 0,
  tags: [] as string[],
  status: 'draft',
})

const form = ref(emptyForm())
const tagInput = ref('')

const renderedHtml = computed(() => {
  if (!selectedArticle.value?.content_md) return '<p class="text-zinc-400 text-sm">暂无内容</p>'
  return marked(selectedArticle.value.content_md || '')
})

function findCatName(id: number): string {
  const find = (nodes: any[]): any => {
    for (const n of nodes) {
      if (n.id === id) return n
      if (n.children?.length) {
        const r = find(n.children)
        if (r) return r
      }
    }
    return null
  }
  return find(categoryTree.value)?.name || ''
}

async function loadCategories() {
  const { data } = await listKbCategories(companyId)
  categoryTree.value = data
  // 默认展开 L1
  data.forEach((n: any) => expandedIds.value.add(n.id))
}

async function loadArticles() {
  const params: Record<string, any> = { limit: pageSize, offset: (page.value - 1) * pageSize }
  if (selectedCategoryId.value) params.category_id = selectedCategoryId.value
  if (searchText.value) params.search = searchText.value
  const { data } = await listKbArticles(companyId, params)
  articles.value = data
}

function onSearch() {
  page.value = 1
  selectedIds.value.clear()
  loadArticles()
}

async function selectArticle(article: any) {
  const { data } = await getKbArticle(article.id)
  selectedArticle.value = data
  editMode.value = false
}

function selectCategory(id: number) {
  selectedCategoryId.value = selectedCategoryId.value === id ? null : id
  selectedArticle.value = null
  page.value = 1
  loadArticles()
}

function toggleExpand(id: number) {
  if (expandedIds.value.has(id)) expandedIds.value.delete(id)
  else expandedIds.value.add(id)
}

// 分类管理
function openCreateCat(parentId: number) {
  catDialogMode.value = 'create'
  catForm.value = { name: '', parent_id: parentId }
  editingCatId.value = null
  catDialogVisible.value = true
}

function openEditCat(cat: any) {
  catDialogMode.value = 'edit'
  catForm.value = { name: cat.name, parent_id: 0 }
  editingCatId.value = cat.id
  catDialogVisible.value = true
}

async function saveCat() {
  if (!catForm.value.name.trim()) return
  try {
    if (catDialogMode.value === 'create') {
      await createKbCategory({
        company_id: companyId,
        name: catForm.value.name.trim(),
        parent_id: catForm.value.parent_id,
      })
      toast.add({ severity: 'success', summary: '分类已创建', life: 2000 })
    } else {
      await updateKbCategory(editingCatId.value!, companyId, { name: catForm.value.name.trim() })
      toast.add({ severity: 'success', summary: '分类已更新', life: 2000 })
    }
    catDialogVisible.value = false
    await loadCategories()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: e?.response?.data?.detail || '操作失败', life: 3000 })
  }
}

async function removeCat(cat: any) {
  if (cat.is_system) {
    toast.add({ severity: 'warn', summary: '系统预置分类不可删除', life: 3000 })
    return
  }
  if (!confirm(`确定删除分类「${cat.name}」？`)) return
  try {
    await deleteKbCategory(cat.id, companyId)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await loadCategories()
    if (selectedCategoryId.value === cat.id) {
      selectedCategoryId.value = null
      loadArticles()
    }
  } catch (e: any) {
    toast.add({ severity: 'error', summary: e?.response?.data?.detail || '需上级批准', life: 3000 })
  }
}

function toggleSelectAll() {
  if (selectedIds.value.size === articles.value.length) {
    selectedIds.value.clear()
  } else {
    articles.value.forEach((a: any) => selectedIds.value.add(a.id))
  }
}

function toggleSelect(id: number) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
}

async function batchDelete() {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确定删除选中的 ${selectedIds.value.size} 篇文章？`)) return
  await fetch('/api/kb/articles/batch-delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
    body: JSON.stringify({ ids: Array.from(selectedIds.value) }),
  })
  toast.add({ severity: 'success', summary: `已删除 ${selectedIds.value.size} 篇`, life: 2000 })
  selectedIds.value.clear()
  await loadArticles()
}

function exportCSV() {
  const a = document.createElement('a')
  a.href = `/api/kb/articles/csv?company_id=${companyId}`
  a.download = '知识库文章.csv'
  a.click()
}

function openCreate() {
  form.value = emptyForm()
  if (selectedCategoryId.value) form.value.category_id = selectedCategoryId.value
  tagInput.value = ''
  editorVisible.value = true
}

function openEdit() {
  const a = selectedArticle.value
  form.value = {
    company_id: companyId,
    title: a.title,
    content_md: a.content_md || '',
    category_id: a.category_id || 0,
    tags: a.tags ? a.tags.split(',').filter(Boolean) : [],
    status: a.status,
  }
  editMode.value = true
  tagInput.value = ''
  editorVisible.value = true
}

function addTag() {
  const t = tagInput.value.trim()
  if (t && !form.value.tags.includes(t)) {
    form.value.tags.push(t)
    tagInput.value = ''
  }
}

function removeTag(t: string) {
  form.value.tags = form.value.tags.filter((x: string) => x !== t)
}

async function save() {
  const payload = { ...form.value }
  if (selectedArticle.value && editMode.value) {
    await updateKbArticle(selectedArticle.value.id, payload)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createKbArticle(payload)
    toast.add({ severity: 'success', summary: '文章已创建', life: 2000 })
  }
  editorVisible.value = false
  selectedArticle.value = null
  await loadArticles()
}

async function remove() {
  if (!selectedArticle.value || !confirm('确定删除该文章？')) return
  await deleteKbArticle(selectedArticle.value.id)
  toast.add({ severity: 'success', summary: '已删除', life: 2000 })
  selectedArticle.value = null
  await loadArticles()
}

async function togglePublish() {
  const a = selectedArticle.value
  const newStatus = a.status === 'published' ? 'draft' : 'published'
  await updateKbArticle(a.id, { status: newStatus })
  toast.add({ severity: 'success', summary: newStatus === 'published' ? '已发布' : '已取消发布', life: 2000 })
  await loadArticles()
  selectArticle({ id: a.id })
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadArticles()])
})
</script>

<template>
  <div class="flex h-full">
    <!-- Left: Category Tree -->
    <div class="w-56 border-r border-dashed border-zinc-200 bg-zinc-50 flex flex-col shrink-0">
      <div class="p-3 border-b border-dashed border-zinc-200 space-y-2">
        <button @click="openCreate" class="w-full px-3 py-2 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">
          + 新建文章
        </button>
        <button @click="exportCSV" class="w-full px-3 py-1.5 border rounded text-xs hover:bg-zinc-100">导出CSV</button>
        <button
          v-if="selectedIds.size > 0"
          @click="batchDelete"
          class="w-full px-3 py-1.5 border border-red-300 text-red-600 rounded text-xs hover:bg-red-50"
        >
          删除选中 ({{ selectedIds.size }})
        </button>
      </div>
      <div class="overflow-auto flex-1">
        <div v-for="cat in categoryTree" :key="cat.id">
          <CategoryTreeNode
            :cat="cat"
            :selected-id="selectedCategoryId"
            :expanded-ids="expandedIds"
            @select="selectCategory"
            @toggle="toggleExpand"
            @add="openCreateCat"
            @edit="openEditCat"
            @remove="removeCat"
          />
        </div>
        <div v-if="categoryTree.length === 0" class="p-4 text-center text-xs text-zinc-400">暂无分类</div>
      </div>
    </div>

    <!-- Center: Article List -->
    <div class="w-72 border-r border-dashed border-zinc-200 flex flex-col shrink-0">
      <div class="p-3 border-b border-dashed border-zinc-200">
        <input
          v-model="searchText"
          @input="onSearch"
          placeholder="搜索标题/正文..."
          class="w-full border rounded px-2 py-1.5 text-xs"
        />
      </div>
      <div class="overflow-auto flex-1">
        <div class="flex items-center px-3 py-1 border-b border-dashed border-zinc-200 text-[10px] text-zinc-400">
          <input
            type="checkbox"
            :checked="selectedIds.size === articles.length && articles.length > 0"
            @change="toggleSelectAll"
            class="mr-2"
          />
          <span>全选</span>
        </div>
        <div
          v-for="article in articles"
          :key="article.id"
          class="flex items-start px-3 py-2.5 border-b border-dashed border-zinc-200 cursor-pointer hover:bg-zinc-50 transition-colors"
          :class="selectedArticle?.id === article.id ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''"
        >
          <input
            type="checkbox"
            :checked="selectedIds.has(article.id)"
            @click.stop
            @change="toggleSelect(article.id)"
            class="mr-2 mt-0.5 shrink-0"
          />
          <div class="flex-1 min-w-0" @click="selectArticle(article)">
            <div class="text-xs font-medium text-zinc-800 truncate">{{ article.title }}</div>
            <div class="flex items-center gap-2 mt-1">
              <span class="text-[10px] text-zinc-400">{{ findCatName(article.category_id) }}</span>
              <span class="text-[10px] text-zinc-300">{{ article.author }}</span>
            </div>
            <div class="flex items-center gap-2 mt-0.5">
              <span
                class="text-[10px] px-1.5 py-0.5 rounded"
                :class="
                  article.status === 'published'
                    ? 'bg-green-100 text-green-700'
                    : article.status === 'archived'
                      ? 'bg-zinc-200 text-zinc-500'
                      : 'bg-amber-100 text-amber-700'
                "
                >{{
                  article.status === 'published' ? '已发布' : article.status === 'archived' ? '已归档' : '草稿'
                }}</span
              >
              <span class="text-[10px] text-zinc-300">v{{ article.version }}</span>
            </div>
          </div>
        </div>
        <div v-if="articles.length === 0" class="p-6 text-center text-xs text-zinc-400">暂无文章</div>
        <div class="flex items-center justify-between px-3 py-2 border-t border-dashed border-zinc-200 text-[10px]">
          <span class="text-zinc-400">第 {{ page }} 页</span>
          <div class="flex gap-1">
            <button
              @click="page = Math.max(1, page - 1); loadArticles()"
              :disabled="page <= 1"
              class="px-2 py-0.5 border rounded disabled:opacity-30"
            >
              上一页
            </button>
            <button
              @click="page = page + 1; loadArticles()"
              class="px-2 py-0.5 border rounded"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Article Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <template v-if="selectedArticle">
        <div class="flex items-center justify-between px-4 py-2 border-b bg-white">
          <div>
            <h1 class="text-base font-bold">{{ selectedArticle.title }}</h1>
            <div class="flex items-center gap-2 text-xs text-zinc-400 mt-0.5">
              <span>{{ selectedArticle.author }}</span>
              <span>·</span>
              <span>v{{ selectedArticle.version }}</span>
              <span>·</span>
              <span>{{ selectedArticle.updated_at?.slice(0, 10) }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="togglePublish"
              class="px-3 py-1 text-xs rounded border"
              :class="
                selectedArticle.status === 'published'
                  ? 'text-amber-600 border-amber-300'
                  : 'text-green-600 border-green-300'
              "
            >
              {{ selectedArticle.status === 'published' ? '取消发布' : '发布' }}
            </button>
            <button @click="openEdit" class="px-3 py-1 text-xs rounded border text-blue-600 border-blue-300">
              编辑
            </button>
            <button @click="remove" class="px-3 py-1 text-xs rounded border text-red-500 border-red-300">删除</button>
          </div>
        </div>
        <div class="flex-1 overflow-auto p-6">
          <div class="prose prose-sm max-w-3xl" v-html="renderedHtml" />
          <div v-if="selectedArticle.tags" class="flex gap-1 mt-6 pt-4 border-t">
            <span
              v-for="t in selectedArticle.tags.split(',').filter(Boolean)"
              :key="t"
              class="text-[10px] bg-zinc-100 text-zinc-500 px-2 py-0.5 rounded"
              >{{ t }}</span
            >
          </div>
        </div>
      </template>
      <div v-else class="flex-1 flex items-center justify-center text-sm text-zinc-400">选择一篇文章查看</div>
    </div>

    <!-- Editor Dialog -->
    <div v-if="editorVisible" class="fixed inset-0 bg-black/40 flex items-start justify-center z-50 pt-10">
      <div class="bg-white rounded-lg w-[800px] max-h-[85vh] flex flex-col">
        <div class="p-4 border-b flex items-center justify-between">
          <h2 class="text-lg font-bold">{{ selectedArticle && !editMode ? '编辑文章' : '新建文章' }}</h2>
          <button @click="editorVisible = false" class="text-zinc-400 hover:text-zinc-600">&times;</button>
        </div>
        <div class="p-4 space-y-3 overflow-auto flex-1">
          <div>
            <label class="text-xs text-zinc-500">标题</label
            ><input v-model="form.title" class="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div class="flex gap-3">
            <div class="flex-1">
              <label class="text-xs text-zinc-500">分类</label>
              <select v-model="form.category_id" class="w-full border rounded px-2 py-1.5 text-sm">
                <option :value="0" disabled>请选择分类</option>
                <optgroup v-for="l1 in categoryTree" :key="l1.id" :label="l1.name">
                  <option :value="l1.id">{{ l1.name }}</option>
                  <template v-for="l2 in l1.children" :key="l2.id">
                    <option :value="l2.id">&nbsp;&nbsp;{{ l2.name }}</option>
                  </template>
                </optgroup>
              </select>
            </div>
            <div class="flex-1">
              <label class="text-xs text-zinc-500">状态</label>
              <select v-model="form.status" class="w-full border rounded px-2 py-1.5 text-sm">
                <option value="draft">草稿</option>
                <option value="published">已发布</option>
                <option value="archived">已归档</option>
              </select>
            </div>
          </div>
          <div>
            <label class="text-xs text-zinc-500">标签</label>
            <div class="flex flex-wrap gap-1 mb-1">
              <span
                v-for="t in form.tags"
                :key="t"
                class="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded flex items-center gap-1"
              >
                {{ t }} <button @click="removeTag(t)" class="text-blue-400 hover:text-red-500">&times;</button>
              </span>
            </div>
            <div class="flex gap-1">
              <input
                v-model="tagInput"
                @keydown.enter.prevent="addTag"
                placeholder="输入标签后回车"
                class="flex-1 border rounded px-2 py-1 text-xs"
              />
              <button @click="addTag" class="px-3 py-1 bg-zinc-100 rounded text-xs hover:bg-zinc-200">添加</button>
            </div>
          </div>
          <div>
            <label class="text-xs text-zinc-500">正文 (Markdown)</label>
            <textarea
              v-model="form.content_md"
              rows="14"
              class="w-full border rounded px-2 py-1.5 text-sm font-mono"
              placeholder="支持 Markdown 格式..."
            ></textarea>
          </div>
        </div>
        <div class="p-4 border-t flex justify-end gap-2">
          <button @click="editorVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>

    <!-- Category Dialog -->
    <div v-if="catDialogVisible" class="fixed inset-0 bg-black/40 flex items-start justify-center z-50 pt-20">
      <div class="bg-white rounded-lg w-96">
        <div class="p-4 border-b flex items-center justify-between">
          <h3 class="font-bold text-sm">{{ catDialogMode === 'create' ? '新增子分类' : '编辑分类' }}</h3>
          <button @click="catDialogVisible = false" class="text-zinc-400 hover:text-zinc-600">&times;</button>
        </div>
        <div class="p-4 space-y-3">
          <div>
            <label class="text-xs text-zinc-500">父分类</label>
            <div class="text-sm text-zinc-700 mt-1">{{ findCatName(catForm.parent_id) || '根目录' }}</div>
          </div>
          <div>
            <label class="text-xs text-zinc-500">分类名称</label>
            <input
              v-model="catForm.name"
              @keydown.enter="saveCat"
              class="w-full border rounded px-2 py-1.5 text-sm mt-1"
              placeholder="输入分类名称"
            />
          </div>
        </div>
        <div class="p-4 border-t flex justify-end gap-2">
          <button @click="catDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="saveCat" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prose :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}
.prose :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}
.prose :deep(h3) {
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}
.prose :deep(p) {
  margin-bottom: 0.75rem;
  line-height: 1.7;
}
.prose :deep(ul),
.prose :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
}
.prose :deep(li) {
  margin-bottom: 0.25rem;
}
.prose :deep(code) {
  background: #f4f4f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.85em;
}
.prose :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin-bottom: 0.75rem;
}
.prose :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}
.prose :deep(blockquote) {
  border-left: 3px solid #e4e4e7;
  padding-left: 1rem;
  color: #71717a;
  margin-bottom: 0.75rem;
}
.prose :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}
.prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 0.75rem;
}
.prose :deep(th),
.prose :deep(td) {
  border: 1px solid #e4e4e7;
  padding: 0.5rem;
  text-align: left;
  font-size: 0.875rem;
}
.prose :deep(th) {
  background: #f4f4f5;
  font-weight: 600;
}
.prose :deep(hr) {
  border: none;
  border-top: 1px solid #e4e4e7;
  margin: 1rem 0;
}
.prose :deep(img) {
  max-width: 100%;
  border-radius: 6px;
}
</style>
