<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Checkbox from 'primevue/checkbox'
import {
  listAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
  importAuxConfig,
} from '@/api'

const accounts = ref<any[]>([])
const loading = ref(false)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const selectedLevel = ref(0)
const selectedCategory = ref('')
const searchText = ref('')
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showSearchDialog = ref(false)
const showAuxDialog = ref(false)
const editTarget = ref<any>(null)
const selectedIds = ref<any[]>([])

// New account form
const newAccount = ref({
  code: '',
  name: '',
  level: 1,
  parent_code: '',
  category: 'asset',
  balance_direction: 'debit',
  auxiliary_items: '',
})

// Edit form
const editAccount = ref({
  code: '',
  name: '',
  level: 0,
  parent_code: '',
  category: 'asset',
  balance_direction: 'debit',
  auxiliary_items: '',
})

const CATEGORY_OPTIONS = [
  { label: '资产', value: 'asset' },
  { label: '负债', value: 'liability' },
  { label: '共同', value: 'common' },
  { label: '权益', value: 'equity' },
  { label: '收入', value: 'revenue' },
  { label: '成本', value: 'cost' },
  { label: '损益', value: 'profit_loss' },
]
const CATEGORY_LABELS: Record<string, string> = Object.fromEntries(CATEGORY_OPTIONS.map(o => [o.value, o.label]))
const DIRECTION_LABELS: Record<string, string> = { debit: '借', credit: '贷' }

const LEVEL_OPTIONS = [
  { label: '全部级次', value: 0 },
  { label: '一级科目', value: 1 },
  { label: '二级科目', value: 2 },
  { label: '三级科目', value: 3 },
  { label: '四级科目', value: 4 },
]

// Filtered accounts
const filteredAccounts = computed(() => {
  let list = accounts.value
  if (selectedLevel.value) list = list.filter(a => a.level === selectedLevel.value)
  if (selectedCategory.value) list = list.filter(a => a.category === selectedCategory.value)
  if (searchText.value) {
    const t = searchText.value.toLowerCase()
    list = list.filter(a => (a.code || '').toLowerCase().includes(t) || (a.name || '').toLowerCase().includes(t))
  }
  return list
})

function formatNumber(val: number | null) {
  if (val === null || val === undefined) return ''
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadAccounts() {
  loading.value = true
  try {
    const res = await listAccounts(companyId.value)
    accounts.value = res.data
  } finally {
    loading.value = false
  }
}

// Toolbar actions
function doNew() {
  newAccount.value = {
    code: '',
    name: '',
    level: 1,
    parent_code: '',
    category: 'asset',
    balance_direction: 'debit',
    auxiliary_items: '',
  }
  showAddDialog.value = true
}

function doEdit(a: any) {
  editTarget.value = a
  editAccount.value = {
    code: a.code,
    name: a.name,
    level: a.level,
    parent_code: a.parent_code,
    category: a.category,
    balance_direction: a.balance_direction,
    auxiliary_items: a.auxiliary_items || '',
  }
  showEditDialog.value = true
}

async function doDelete(a: any) {
  if (!confirm(`确认删除科目「${a.name}」？`)) return
  try {
    await deleteAccount(a.id)
    await loadAccounts()
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function doCopy(a: any) {
  newAccount.value = {
    code: '',
    name: a.name + ' (复制)',
    level: a.level,
    parent_code: a.parent_code,
    category: a.category,
    balance_direction: a.balance_direction,
    auxiliary_items: a.auxiliary_items || '',
  }
  showAddDialog.value = true
}

// ── 辅助核算设置 ──
const selectedAuxAccountId = ref<number | null>(null)
const auxForm = ref({ dept: false, person: false, customer: false, supplier: false, project: false })

function doAuxSetup(a?: any) {
  if (a) {
    selectedAuxAccountId.value = a.id
    auxForm.value = {
      dept: !!a.aux_dept,
      person: !!a.aux_person,
      customer: !!a.aux_counterparty,
      supplier: false,
      project: !!a.aux_project,
    }
  } else {
    // Toolbar button: pick first account (legacy behavior)
    if (!accounts.value.length) { alert('暂无科目'); return }
    const first = accounts.value[0]
    selectedAuxAccountId.value = first.id
    auxForm.value = {
      dept: !!first.aux_dept,
      person: !!first.aux_person,
      customer: !!first.aux_counterparty,
      supplier: false,
      project: !!first.aux_project,
    }
  }
  showAuxDialog.value = true
}

async function saveAuxSettings() {
  if (!selectedAuxAccountId.value) return
  try {
    await updateAccount(selectedAuxAccountId.value, {
      aux_dept: auxForm.value.dept ? 1 : 0,
      aux_person: auxForm.value.person ? 1 : 0,
      aux_counterparty: (auxForm.value.customer || auxForm.value.supplier) ? 1 : 0,
      aux_project: auxForm.value.project ? 1 : 0,
    })
    showAuxDialog.value = false
    await loadAccounts()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  }
}

function doSearch() {
  showSearchDialog.value = true
}
async function doImport() {
  try {
    const res = await importAuxConfig(companyId.value)
    alert(`辅助核算配置导入完成：更新 ${res.data.updated} 个科目`)
    await loadAccounts()
  } catch (e: any) {
    alert(e.response?.data?.detail || '导入失败')
  }
}
function doExport() {
  const csv = ['编码,名称,级次,类型,余额方向,期初余额']
  for (const a of accounts.value) {
    csv.push([a.code, a.name, a.level, a.category, a.balance_direction, a.initial_balance].join(','))
  }
  const blob = new Blob(['﻿' + csv.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '科目列表.csv'
  link.click()
  URL.revokeObjectURL(url)
}
function doCompare() {
  alert('科目对照功能待开发')
}
function doPrint() {
  window.print()
}

async function handleAdd() {
  try {
    await createAccount({
      company_id: companyId.value,
      code: newAccount.value.code,
      name: newAccount.value.name,
      level: newAccount.value.level,
      parent_code: newAccount.value.parent_code || undefined,
      category: newAccount.value.category,
      balance_direction: newAccount.value.balance_direction,
      initial_balance: 0,
    })
    showAddDialog.value = false
    await loadAccounts()
  } catch (e: any) {
    alert(e.response?.data?.detail || '添加失败')
  }
}

async function handleEdit() {
  try {
    const data: Record<string, any> = {}
    if (editAccount.value.name !== editTarget.value.name) data.name = editAccount.value.name
    if (editAccount.value.code !== editTarget.value.code && !editTarget.value.is_system) data.code = editAccount.value.code
    if (editAccount.value.level !== editTarget.value.level) data.level = editAccount.value.level
    if (editAccount.value.category !== editTarget.value.category) data.category = editAccount.value.category
    if (editAccount.value.balance_direction !== editTarget.value.balance_direction) data.balance_direction = editAccount.value.balance_direction
    if (editAccount.value.parent_code !== (editTarget.value.parent_code || '')) data.parent_code = editAccount.value.parent_code || undefined
    if (Object.keys(data).length === 0) { showEditDialog.value = false; return }
    await updateAccount(editTarget.value.id, data)
    showEditDialog.value = false
    await loadAccounts()
  } catch (e: any) {
    alert(e.response?.data?.detail || '修改失败')
  }
}

function toggleSelectAll(e: Event) {
  const checked = (e.target as HTMLInputElement).checked
  selectedIds.value = checked ? filteredAccounts.value.map(a => a.id) : []
}

function toggleSelect(id: number) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

const _levelIndent = ['', '  ', '    ', '      ', '        ']

onMounted(loadAccounts)
</script>

<template>
  <div>
    <!-- Stats bar -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-4 text-xs text-stone-500">
        <span class="font-medium">科目级次：4-4-2</span>
        <span class="border-l border-stone-300 pl-4"
          >科目个数：<strong class="text-stone-700">{{ accounts.length }}</strong></span
        >
      </div>
      <div class="flex items-center gap-2">
        <Dropdown
          v-model="selectedLevel"
          :options="LEVEL_OPTIONS"
          optionLabel="label"
          optionValue="value"
          class="w-32"
          @change="() => {}"
        />
        <Dropdown
          v-model="selectedCategory"
          :options="CATEGORY_OPTIONS"
          optionLabel="label"
          optionValue="value"
          class="w-28"
          @change="() => {}"
          placeholder="类别"
        />
      </div>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <Button label="新增" icon="pi pi-plus" text size="small" @click="doNew" />
      <Button
        label="修改"
        icon="pi pi-pencil"
        text
        size="small"
        @click="editTarget && doEdit(editTarget)"
        :disabled="!editTarget"
      />
      <Button
        label="删除"
        icon="pi pi-trash"
        text
        severity="danger"
        size="small"
        @click="editTarget && doDelete(editTarget)"
        :disabled="!editTarget"
      />
      <Button
        label="复制"
        icon="pi pi-copy"
        text
        size="small"
        @click="editTarget && doCopy(editTarget)"
        :disabled="!editTarget"
      />
      <span class="border-r border-stone-200 mx-1" />
      <Button label="辅助核算设置" icon="pi pi-cog" text size="small"
        @click="doAuxSetup(editTarget || undefined)" />
      <Button label="查找" icon="pi pi-search" text size="small" @click="doSearch" />
      <Button label="栏目" icon="pi pi-table" text size="small" />
      <span class="border-r border-stone-200 mx-1" />
      <Button label="导入" icon="pi pi-upload" text size="small" @click="doImport" />
      <Button label="导出" icon="pi pi-download" text size="small" @click="doExport" />
      <Button label="科目对照" icon="pi pi-th-large" text size="small" @click="doCompare" />
      <span class="border-r border-stone-200 mx-1" />
      <Button label="打印" icon="pi pi-print" text size="small" @click="doPrint" />
      <Button label="退出" icon="pi pi-times" text severity="secondary" size="small" @click="$router.push('')" />
    </div>

    <!-- Data table -->
    <div class="table-compact">
      <table class="data-table">
        <thead>
          <tr>
            <th class="w-8 text-center">
              <input type="checkbox" @change="toggleSelectAll" class="rounded-sm border-stone-300" />
            </th>
            <th class="w-12 text-center">序号</th>
            <th class="w-14 text-center">级次</th>
            <th class="w-24">科目编码</th>
            <th>科目名称</th>
            <th class="w-24">科目类型</th>
            <th class="w-32 text-right">余额</th>
            <th class="w-16 text-center">余额方向</th>
            <th class="w-24 text-center">辅助核算</th>
            <th class="w-20 text-center">账页格式</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(a, idx) in filteredAccounts"
            :key="a.id"
            class="cursor-pointer transition-colors"
            :class="{ 'bg-amber-50/50': selectedIds.includes(a.id) }"
            @click="editTarget = a"
          >
            <td class="text-center">
              <input
                type="checkbox"
                :checked="selectedIds.includes(a.id)"
                @change="toggleSelect(a.id)"
                @click.stop
                class="rounded-sm border-stone-300"
              />
            </td>
            <td class="text-center text-stone-400">{{ idx + 1 }}</td>
            <td class="text-center text-stone-400">{{ a.level || 1 }}</td>
            <td class="font-mono text-xs tracking-wide">{{ a.code }}</td>
            <td :style="{ paddingLeft: `${12 + (a.level - 1) * 16}px` }">
              {{ a.name }}
            </td>
            <td class="text-stone-500 text-xs">
              <span class="inline-block px-1.5 py-0.5 rounded-sm bg-stone-100">{{
                CATEGORY_LABELS[a.category] || a.category
              }}</span>
            </td>
            <td class="report-number text-stone-600">{{ formatNumber(a.initial_balance) }}</td>
            <td class="text-center text-xs">{{ DIRECTION_LABELS[a.balance_direction] || '' }}</td>
            <td class="text-center text-xs text-stone-400">{{ a.auxiliary_items || '-' }}</td>
            <td class="text-center text-xs text-stone-400">金额式</td>
          </tr>
          <tr v-if="!filteredAccounts.length">
            <td colspan="10" class="py-12 text-center text-stone-400">暂无科目数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add dialog -->
    <Dialog v-model:visible="showAddDialog" header="新增科目" :style="{ width: '500px' }">
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">科目编码</label>
            <InputText v-model="newAccount.code" class="w-full" placeholder="如：100201" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">科目名称</label>
            <InputText v-model="newAccount.name" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">科目级次</label>
            <Dropdown
              v-model="newAccount.level"
              :options="LEVEL_OPTIONS.filter(o => o.value > 0)"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">科目类型</label>
            <Dropdown
              v-model="newAccount.category"
              :options="CATEGORY_OPTIONS"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">余额方向</label>
            <Dropdown
              v-model="newAccount.balance_direction"
              :options="[
                { label: '借', value: 'debit' },
                { label: '贷', value: 'credit' },
              ]"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">父科目编码（可选）</label>
            <InputText v-model="newAccount.parent_code" class="w-full" placeholder="如：1002" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showAddDialog = false" />
        <Button label="保存" icon="pi pi-check" @click="handleAdd" :disabled="!newAccount.code || !newAccount.name" />
      </template>
    </Dialog>

    <!-- Edit dialog -->
    <Dialog v-model:visible="showEditDialog" header="修改科目" :style="{ width: '500px' }" :modal="true">
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">科目编码</label>
            <InputText v-model="editAccount.code" class="w-full" :disabled="editTarget?.is_system" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">科目名称</label>
            <InputText v-model="editAccount.name" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">科目级次</label>
            <Dropdown
              v-model="editAccount.level"
              :options="LEVEL_OPTIONS.filter(o => o.value > 0)"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              :disabled="editTarget?.is_system"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">科目类型</label>
            <Dropdown
              v-model="editAccount.category"
              :options="CATEGORY_OPTIONS"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              :disabled="editTarget?.is_system"
            />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">父科目编码（可选）</label>
          <InputText v-model="editAccount.parent_code" class="w-full" placeholder="如：1002" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showEditDialog = false" />
        <Button label="保存" icon="pi pi-check" @click="handleEdit" />
      </template>
    </Dialog>

    <!-- Search dialog -->
    <Dialog v-model:visible="showSearchDialog" header="查找科目" :style="{ width: '400px' }">
      <div class="flex flex-col gap-4 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">关键字（编码/名称）</label>
          <InputText v-model="searchText" class="w-full" placeholder="输入后按回车查找" @keyup.enter="() => {}" />
        </div>
        <div class="flex gap-2">
          <Button label="查找" icon="pi pi-search" @click="showSearchDialog = false" />
          <Button
            label="清除"
            icon="pi pi-refresh"
            text
            @click="searchText = ''; showSearchDialog = false"
          />
        </div>
      </div>
    </Dialog>

    <!-- Auxiliary dialog -->
    <Dialog v-model:visible="showAuxDialog" header="辅助核算设置" :style="{ width: '500px' }" :modal="true">
      <div class="flex flex-col gap-4 py-4">
        <p class="text-sm text-zinc-500">选择启用的辅助核算项目：</p>
        <div class="flex items-center gap-2">
          <Checkbox inputId="aux_dept" v-model="auxForm.dept" />
          <label for="aux_dept" class="text-sm text-zinc-600 cursor-pointer">部门核算</label>
        </div>
        <div class="flex items-center gap-2">
          <Checkbox inputId="aux_person" v-model="auxForm.person" />
          <label for="aux_person" class="text-sm text-zinc-600 cursor-pointer">人员核算</label>
        </div>
        <div class="flex items-center gap-2">
          <Checkbox inputId="aux_customer" v-model="auxForm.customer" />
          <label for="aux_customer" class="text-sm text-zinc-600 cursor-pointer">客户核算</label>
        </div>
        <div class="flex items-center gap-2">
          <Checkbox inputId="aux_supplier" v-model="auxForm.supplier" />
          <label for="aux_supplier" class="text-sm text-zinc-600 cursor-pointer">供应商核算</label>
        </div>
        <div class="flex items-center gap-2">
          <Checkbox inputId="aux_project" v-model="auxForm.project" />
          <label for="aux_project" class="text-sm text-zinc-600 cursor-pointer">项目核算</label>
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showAuxDialog = false" />
        <Button label="保存设置" icon="pi pi-check" @click="saveAuxSettings" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
@media print {
  @page {
    size: A4 landscape;
    margin: 10mm;
  }
}
</style>
