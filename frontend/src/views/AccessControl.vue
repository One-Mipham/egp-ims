<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import SelectButton from 'primevue/selectbutton'
import { listAccessRecords, createAccessRecord, deleteAccessRecord } from '@/api'

const records = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filterDirection = ref<string | null>(null)
const filterName = ref('')

const showDialog = ref(false)
const form = ref({
  person_name: '',
  department: '',
  phone: '',
  direction: 'entry',
  access_point: '',
  reason: '',
  notes: '',
})

const DIR_OPTIONS = [
  { label: '全部', value: null },
  { label: '进入', value: 'entry' },
  { label: '离开', value: 'exit' },
]
const DIR_LABELS: Record<string, string> = { entry: '进入', exit: '离开' }
const DIR_COLORS: Record<string, string> = {
  entry: 'bg-emerald-100 text-emerald-700',
  exit: 'bg-orange-100 text-orange-700',
}

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await listAccessRecords(cid, page.value, 20, filterDirection.value, filterName.value || undefined)
    records.value = res.data.records || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { person_name: '', department: '', phone: '', direction: 'entry', access_point: '', reason: '', notes: '' }
  showDialog.value = true
}

async function handleSave() {
  const cid = parseInt(localStorage.getItem('companyId') || '1')
  await createAccessRecord(cid, form.value.person_name, form.value.direction, form.value.department, form.value.phone, form.value.access_point, form.value.reason, form.value.notes)
  showDialog.value = false
  page.value = 1
  await load()
}

async function handleDelete(id: number) {
  if (!confirm('确定删除该记录？')) return
  await deleteAccessRecord(id)
  await load()
}

function changePage(delta: number) {
  const maxPage = Math.ceil(total.value / 20) || 1
  page.value = Math.max(1, Math.min(maxPage, page.value + delta))
  load()
}

onMounted(load)
</script>

<template>
  <div class="max-w-5xl">
    <h2 class="text-lg font-bold mb-1">门禁管理</h2>
    <p class="text-xs text-zinc-400 mb-4">人员出入记录登记与查询</p>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2 items-center mb-4">
      <SelectButton
        v-model="filterDirection"
        :options="DIR_OPTIONS"
        option-label="label"
        option-value="value"
        size="small"
        @change="page = 1; load()"
      />
      <InputText v-model="filterName" placeholder="搜索人员..." size="small" class="w-40" @keyup.enter="page = 1; load()" />
      <Button label="登记出入" icon="pi pi-plus" size="small" severity="success" @click="openCreate" />
    </div>

    <!-- Table -->
    <div v-if="loading" class="text-sm text-zinc-400 py-8 text-center">加载中...</div>

    <div v-else-if="!records.length" class="text-sm text-zinc-400 py-8 text-center">暂无出入记录。</div>

    <div v-else class="bg-white border rounded overflow-x-auto">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="border-b bg-stone-50 text-left text-xs text-zinc-500">
            <th class="py-2 px-3">时间</th>
            <th class="py-2 px-3">姓名</th>
            <th class="py-2 px-3">部门</th>
            <th class="py-2 px-3">方向</th>
            <th class="py-2 px-3">门禁点</th>
            <th class="py-2 px-3">事由</th>
            <th class="py-2 px-3">电话</th>
            <th class="py-2 px-3 w-16">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in records" :key="r.id" class="border-b last:border-b-0 hover:bg-stone-50">
            <td class="py-1.5 px-3 text-xs whitespace-nowrap">{{ r.record_time?.replace('T', ' ').slice(0, 16) }}</td>
            <td class="py-1.5 px-3 font-medium">{{ r.person_name }}</td>
            <td class="py-1.5 px-3 text-xs text-zinc-500">{{ r.department || '-' }}</td>
            <td class="py-1.5 px-3">
              <span class="text-xs px-1.5 py-0.5 rounded" :class="DIR_COLORS[r.direction]">{{ DIR_LABELS[r.direction] }}</span>
            </td>
            <td class="py-1.5 px-3 text-xs text-zinc-500">{{ r.access_point || '-' }}</td>
            <td class="py-1.5 px-3 text-xs max-w-xs truncate">{{ r.reason || '-' }}</td>
            <td class="py-1.5 px-3 text-xs text-zinc-400">{{ r.phone || '-' }}</td>
            <td class="py-1.5 px-3">
              <Button icon="pi pi-trash" size="small" text rounded severity="danger" @click="handleDelete(r.id)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > 20" class="flex gap-2 items-center justify-center mt-3">
      <Button icon="pi pi-chevron-left" size="small" text :disabled="page <= 1" @click="changePage(-1)" />
      <span class="text-xs text-zinc-500">第 {{ page }} 页 / 共 {{ Math.ceil(total / 20) }} 页 ({{ total }} 条)</span>
      <Button icon="pi pi-chevron-right" size="small" text :disabled="page >= Math.ceil(total / 20)" @click="changePage(1)" />
    </div>

    <!-- Dialog -->
    <Dialog v-model:visible="showDialog" header="登记出入记录" :modal="true" class="w-full max-w-md">
      <div class="space-y-3">
        <div>
          <label class="text-xs text-zinc-500 block mb-1">姓名 *</label>
          <InputText v-model="form.person_name" class="w-full" placeholder="人员姓名" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 block mb-1">部门</label>
            <InputText v-model="form.department" class="w-full" placeholder="部门" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 block mb-1">电话</label>
            <InputText v-model="form.phone" class="w-full" placeholder="联系电话" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 block mb-1">方向 *</label>
            <select v-model="form.direction" class="border rounded px-2 py-1.5 text-sm w-full">
              <option value="entry">进入</option>
              <option value="exit">离开</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500 block mb-1">门禁点</label>
            <select v-model="form.access_point" class="border rounded px-2 py-1.5 text-sm w-full">
              <option value="">请选择</option>
              <option value="正门">正门</option>
              <option value="侧门">侧门</option>
              <option value="车库入口">车库入口</option>
              <option value="后门">后门</option>
              <option value="机房">机房</option>
            </select>
          </div>
        </div>
        <div>
          <label class="text-xs text-zinc-500 block mb-1">事由</label>
          <InputText v-model="form.reason" class="w-full" placeholder="来访事由" />
        </div>
        <div>
          <label class="text-xs text-zinc-500 block mb-1">备注</label>
          <InputText v-model="form.notes" class="w-full" placeholder="其他备注" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" size="small" text @click="showDialog = false" />
        <Button label="保存" size="small" icon="pi pi-check" @click="handleSave" :disabled="!form.person_name" />
      </template>
    </Dialog>
  </div>
</template>
