<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dialog from 'primevue/dialog'
import SelectButton from 'primevue/selectbutton'
import { listTasks, createTask, updateTask, deleteTask } from '@/api'

const tasks = ref<any[]>([])
const loading = ref(false)
const filterStatus = ref<string | null>(null)
const filterPriority = ref<string | null>(null)

const showDialog = ref(false)
const editTask = ref<any>(null)
const form = ref({ title: '', description: '', priority: 'medium', due_date: '' })

const STATUS_OPTIONS = [
  { label: '全部', value: null },
  { label: '待处理', value: 'pending' },
  { label: '已完成', value: 'completed' },
]
const PRIORITY_OPTIONS = [
  { label: '全部', value: null },
  { label: '高', value: 'high' },
  { label: '中', value: 'medium' },
  { label: '低', value: 'low' },
]

const PRIORITY_LABELS: Record<string, string> = { high: '高', medium: '中', low: '低' }
const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-zinc-100 text-zinc-600',
}

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await listTasks(cid, filterStatus.value, filterPriority.value)
    tasks.value = res.data.tasks || []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editTask.value = null
  form.value = { title: '', description: '', priority: 'medium', due_date: '' }
  showDialog.value = true
}

function openEdit(task: any) {
  editTask.value = task
  form.value = {
    title: task.title,
    description: task.description || '',
    priority: task.priority || 'medium',
    due_date: task.due_date || '',
  }
  showDialog.value = true
}

async function handleSave() {
  const cid = parseInt(localStorage.getItem('companyId') || '1')
  if (editTask.value) {
    await updateTask(editTask.value.id, form.value.title, form.value.description, undefined, form.value.priority, form.value.due_date)
  } else {
    await createTask(cid, form.value.title, form.value.description, form.value.priority, form.value.due_date)
  }
  showDialog.value = false
  await load()
}

async function handleToggle(task: any) {
  const newStatus = task.status === 'completed' ? 'pending' : 'completed'
  await updateTask(task.id, undefined, undefined, newStatus)
  await load()
}

async function handleDelete(task: any) {
  if (!confirm('确定删除该任务？')) return
  await deleteTask(task.id)
  await load()
}

const pendingCount = computed(() => tasks.value.filter(t => t.status === 'pending').length)

onMounted(load)
</script>

<template>
  <div class="max-w-4xl">
    <div class="flex gap-2 items-center mb-1">
      <h2 class="text-lg font-bold">协同办公</h2>
      <span class="text-xs text-zinc-400 ml-2">{{ pendingCount }} 项待处理</span>
    </div>
    <p class="text-xs text-zinc-400 mb-4">内部任务与待办事项管理</p>

    <!-- Filters + Add -->
    <div class="flex flex-wrap gap-2 items-center mb-4">
      <SelectButton
        v-model="filterStatus"
        :options="STATUS_OPTIONS"
        option-label="label"
        option-value="value"
        size="small"
        @change="load"
      />
      <SelectButton
        v-model="filterPriority"
        :options="PRIORITY_OPTIONS"
        option-label="label"
        option-value="value"
        size="small"
        @change="load"
      />
      <Button label="新建任务" icon="pi pi-plus" size="small" severity="success" @click="openCreate" />
    </div>

    <!-- Task list -->
    <div v-if="loading" class="text-sm text-zinc-400 py-8 text-center">加载中...</div>

    <div v-else-if="!tasks.length" class="text-sm text-zinc-400 py-8 text-center">暂无任务，点击"新建任务"开始。</div>

    <div v-else class="space-y-2">
      <div
        v-for="t in tasks"
        :key="t.id"
        class="bg-white border rounded p-3 flex items-start gap-3 hover:shadow-sm transition-shadow"
        :class="{ 'opacity-60': t.status === 'completed' }"
      >
        <!-- Checkbox -->
        <input
          type="checkbox"
          :checked="t.status === 'completed'"
          class="mt-1 w-4 h-4 cursor-pointer accent-emerald-600"
          @change="handleToggle(t)"
        />

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex gap-2 items-center flex-wrap">
            <span class="font-medium text-sm" :class="{ 'line-through': t.status === 'completed' }">{{ t.title }}</span>
            <span class="text-xs px-1.5 py-0.5 rounded" :class="PRIORITY_COLORS[t.priority]">{{ PRIORITY_LABELS[t.priority] }}</span>
          </div>
          <p v-if="t.description" class="text-xs text-zinc-500 mt-0.5 line-clamp-2">{{ t.description }}</p>
          <div class="flex gap-3 text-xs text-zinc-400 mt-1">
            <span v-if="t.due_date">截止: {{ t.due_date }}</span>
            <span>创建: {{ t.created_at?.slice(0, 10) }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-1 shrink-0">
          <Button icon="pi pi-pencil" size="small" text rounded severity="info" @click="openEdit(t)" />
          <Button icon="pi pi-trash" size="small" text rounded severity="danger" @click="handleDelete(t)" />
        </div>
      </div>
    </div>

    <!-- Dialog -->
    <Dialog v-model:visible="showDialog" :header="editTask ? '编辑任务' : '新建任务'" :modal="true" class="w-full max-w-lg">
      <div class="space-y-3">
        <div>
          <label class="text-xs text-zinc-500 block mb-1">标题 *</label>
          <InputText v-model="form.title" class="w-full" placeholder="任务标题" />
        </div>
        <div>
          <label class="text-xs text-zinc-500 block mb-1">描述</label>
          <Textarea v-model="form.description" rows="2" class="w-full" placeholder="任务描述（可选）" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 block mb-1">优先级</label>
            <select v-model="form.priority" class="border rounded px-2 py-1.5 text-sm w-full">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500 block mb-1">截止日期</label>
            <input v-model="form.due_date" type="date" class="border rounded px-2 py-1.5 text-sm w-full" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="取消" size="small" text @click="showDialog = false" />
        <Button label="保存" size="small" icon="pi pi-check" @click="handleSave" :disabled="!form.title" />
      </template>
    </Dialog>
  </div>
</template>
