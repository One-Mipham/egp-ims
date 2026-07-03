<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import { listDepartments, createDepartment, deleteDepartment, bulkImportDepartments } from '@/api'

const departments = ref<any[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const importText = ref('')
const importResult = ref('')
const newDept = ref({ code: '', name: '', manager: '' })
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

async function handleAdd() {
  if (!newDept.value.code || !newDept.value.name) return
  try {
    await createDepartment({ company_id: companyId.value, ...newDept.value })
    showAddDialog.value = false
    newDept.value = { code: '', name: '', manager: '' }
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '添加失败')
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
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto max-w-fit min-w-full">
      <DataTable :value="departments" :loading="loading" stripedRows class="shadow-sm" tableStyle="min-width: auto">
        <Column field="code" header="部门编码" sortable style="width: 100px" />
        <Column field="name" header="部门名称" sortable style="width: 160px" />
        <Column field="manager" header="负责人" style="width: 100px" />
        <Column header="状态" style="width: 70px">
          <template #body="{ data }">
            <Tag :value="data.is_active ? '启用' : '停用'" :severity="data.is_active ? 'success' : 'danger'" />
          </template>
        </Column>
        <Column header="操作" style="width: 80px">
          <template #body="{ data }">
            <Button
              v-if="data.is_active"
              label="停用"
              text
              severity="danger"
              size="small"
              @click="handleDelete(data.id)"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showAddDialog" header="新增部门" :style="{ width: '400px' }">
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
        <Button label="保存" icon="pi pi-check" @click="handleAdd" />
      </div>
    </Dialog>

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
