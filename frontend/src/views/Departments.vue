<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import { listDepartments, createDepartment, updateDepartment, deleteDepartment, bulkImportDepartments } from '@/api'

const departments = ref<any[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showImportDialog = ref(false)
const importText = ref('')
const importResult = ref('')
const editTarget = ref<any>(null)
const newDept = ref({ code: '', name: '', manager: '', parent_id: null as number | null })
const editDept = ref({ code: '', name: '', manager: '', parent_id: null as number | null })
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

async function load() {
  loading.value = true
  try {
    const res = await listDepartments(companyId.value)
    departments.value = res.data
  } finally {
    loading.value = false
  }
}

// ── Parent options (exclude self when editing) ──
function parentOptions(excludeId?: number) {
  return departments.value
    .filter(d => d.id !== excludeId)
    .map(d => ({ label: `${d.code} ${d.name}`, value: d.id }))
}

function getLevel(dept: any): number {
  if (!dept.parent_id) return 1
  const seen = new Set<number>()
  let level = 1
  let current = dept
  while (current.parent_id && !seen.has(current.id)) {
    seen.add(current.id)
    level++
    current = departments.value.find(d => d.id === current.parent_id)
    if (!current) break
  }
  return level
}

// Sort departments: parent first, then children
const sortedDepartments = computed(() => {
  const depts = [...departments.value]
  // Build parent map
  const byParent = new Map<number | null, any[]>()
  for (const d of depts) {
    const pid = d.parent_id || null
    if (!byParent.has(pid)) byParent.set(pid, [])
    byParent.get(pid)!.push(d)
  }
  // Flatten recursively
  const result: any[] = []
  function walk(pid: number | null) {
    const children = byParent.get(pid) || []
    children.sort((a, b) => a.code.localeCompare(b.code))
    for (const c of children) {
      result.push(c)
      walk(c.id)
    }
  }
  walk(null)
  return result
})

async function handleAdd() {
  if (!newDept.value.code || !newDept.value.name) return
  try {
    await createDepartment({
      company_id: companyId.value,
      code: newDept.value.code,
      name: newDept.value.name,
      manager: newDept.value.manager || undefined,
      parent_id: newDept.value.parent_id || undefined,
    })
    showAddDialog.value = false
    newDept.value = { code: '', name: '', manager: '', parent_id: null }
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '添加失败')
  }
}

function doEdit(dept: any) {
  editTarget.value = dept
  editDept.value = {
    code: dept.code,
    name: dept.name,
    manager: dept.manager || '',
    parent_id: dept.parent_id || null,
  }
  showEditDialog.value = true
}

async function handleEdit() {
  if (!editTarget.value) return
  try {
    const data: Record<string, any> = {}
    if (editDept.value.name !== editTarget.value.name) data.name = editDept.value.name
    if (editDept.value.code !== editTarget.value.code) data.code = editDept.value.code
    if (editDept.value.manager !== (editTarget.value.manager || '')) data.manager = editDept.value.manager || null
    if (editDept.value.parent_id !== (editTarget.value.parent_id || null)) data.parent_id = editDept.value.parent_id || null
    if (Object.keys(data).length === 0) { showEditDialog.value = false; return }
    await updateDepartment(editTarget.value.id, data)
    showEditDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '修改失败')
  }
}

function parseImportText(text: string) {
  return text
    .trim()
    .split('\n')
    .map(line => {
      const cols = line.split(/\t+/)
      if (cols.length < 2) return null
      return {
        code: cols[0]?.trim() || '',
        name: cols[1]?.trim() || '',
        manager: cols[2]?.trim() || '',
        is_active: cols[3]?.trim() || '是',
      }
    })
    .filter(Boolean)
}

async function handleImport() {
  const rows = parseImportText(importText.value)
  if (!rows.length) {
    importResult.value = '未解析到有效数据，请检查格式'
    return
  }
  importResult.value = '导入中...'
  try {
    const res = await bulkImportDepartments(companyId.value, rows)
    importResult.value = `成功导入 ${res.data.imported} 条${res.data.errors.length ? '，错误：' + res.data.errors.join('；') : ''}`
    importText.value = ''
    showImportDialog.value = false
    await load()
  } catch (e: any) {
    importResult.value = '导入失败：' + (e.response?.data?.detail || e.message)
  }
}

async function handleDelete(id: number) {
  if (!confirm('确定停用此部门？')) return
  try {
    await deleteDepartment(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail)
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2">
        <Button
          label="导入"
          icon="pi pi-upload"
          severity="secondary"
          @click="showImportDialog = true; importResult = ''"
        />
        <Button label="新增部门" icon="pi pi-plus" @click="showAddDialog = true" />
      </div>
    </div>

    <div class="bg-white rounded-sm shadow-sm">
      <DataTable :value="sortedDepartments" :loading="loading" stripedRows class="text-sm" size="small">
        <Column field="code" header="编码" class="font-mono text-xs" />
        <Column header="部门名称">
          <template #body="{ data }">
            <span :style="{ paddingLeft: `${(getLevel(data) - 1) * 20}px` }">
              {{ data.name }}
            </span>
          </template>
        </Column>
        <Column field="manager" header="负责人" />
        <Column header="状态">
          <template #body="{ data }">
            <Tag :value="data.is_active ? '启用' : '停用'" :severity="data.is_active ? 'success' : 'danger'" />
          </template>
        </Column>
        <Column header="操作" class="w-32">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button label="编辑" icon="pi pi-pencil" text size="small" @click="doEdit(data)" />
              <Button label="停用" icon="pi pi-ban" text size="small" severity="danger" @click="handleDelete(data.id)" />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Add dialog -->
    <Dialog v-model:visible="showAddDialog" header="新增部门" :style="{ width: '450px' }">
      <div class="flex flex-col gap-4 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">部门编码</label>
          <InputText v-model="newDept.code" class="w-full" placeholder="如：01" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">部门名称</label>
          <InputText v-model="newDept.name" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">负责人</label>
          <InputText v-model="newDept.manager" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">上级部门（可选）</label>
          <Dropdown
            v-model="newDept.parent_id"
            :options="parentOptions()"
            optionLabel="label"
            optionValue="value"
            class="w-full"
            placeholder="无（一级部门）"
            :showClear="true"
          />
        </div>
        <Button label="保存" icon="pi pi-check" @click="handleAdd" :disabled="!newDept.code || !newDept.name" />
      </div>
    </Dialog>

    <!-- Edit dialog -->
    <Dialog v-model:visible="showEditDialog" header="修改部门" :style="{ width: '450px' }">
      <div class="flex flex-col gap-4 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">部门编码</label>
          <InputText v-model="editDept.code" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">部门名称</label>
          <InputText v-model="editDept.name" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">负责人</label>
          <InputText v-model="editDept.manager" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">上级部门（可选）</label>
          <Dropdown
            v-model="editDept.parent_id"
            :options="parentOptions(editTarget?.id)"
            optionLabel="label"
            optionValue="value"
            class="w-full"
            placeholder="无（一级部门）"
            :showClear="true"
          />
        </div>
        <Button label="保存" icon="pi pi-check" @click="handleEdit" />
      </div>
    </Dialog>

    <!-- Import dialog -->
    <Dialog v-model:visible="showImportDialog" header="导入部门" :style="{ width: '600px' }">
      <div class="flex flex-col gap-4 py-4">
        <div class="text-xs text-zinc-500">
          从 Excel/表格直接复制粘贴，每行一列：<b>部门编码 → 部门名称 → 负责人 → 停用</b>（Tab 分隔）
        </div>
        <textarea
          v-model="importText"
          rows="12"
          class="w-full border border-zinc-300 rounded-sm p-2 text-sm font-mono focus:ring-1 focus:ring-zinc-400 outline-none"
          placeholder="001	董事会"
        />
        <p
          v-if="importResult"
          :class="importResult.includes('错误') || importResult.includes('失败') ? 'text-red-700' : 'text-emerald-600'"
          class="text-sm tracking-wide"
        >
          {{ importResult }}
        </p>
        <Button label="确认导入" icon="pi pi-check" @click="handleImport" :disabled="!importText" />
      </div>
    </Dialog>
  </div>
</template>
