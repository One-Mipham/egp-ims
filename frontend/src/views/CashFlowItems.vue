<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import ToggleSwitch from 'primevue/toggleswitch'
import {
  listCashFlowItems,
  createCashFlowItem,
  updateCashFlowItem,
  deleteCashFlowItem,
  seedDefaultCashFlowItems,
} from '@/api'

const toast = useToast()
const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

interface CFItemForm {
  code: string
  name: string
  category_code: string
  direction: string
  debit_accounts: string
  credit_accounts: string
  is_active: boolean
}

const emptyForm = (): CFItemForm => ({
  code: '',
  name: '',
  category_code: '',
  direction: 'inflow',
  debit_accounts: '',
  credit_accounts: '',
  is_active: true,
})

const form = ref<CFItemForm>(emptyForm())

const CATEGORY_OPTIONS = [
  { label: '销售商品收到现金', value: 'op_sales' },
  { label: '税费返还', value: 'op_refund' },
  { label: '其他经营流入', value: 'op_other_in' },
  { label: '购买商品支付现金', value: 'op_goods' },
  { label: '支付职工', value: 'op_staff' },
  { label: '支付税费', value: 'op_tax' },
  { label: '其他经营流出', value: 'op_other_out' },
  { label: '收回投资', value: 'inv_recover' },
  { label: '投资收益', value: 'inv_income' },
  { label: '处置资产收回', value: 'inv_assets' },
  { label: '购建固定资产支付', value: 'inv_build' },
  { label: '投资支付', value: 'inv_pay' },
  { label: '吸收投资', value: 'fin_invest' },
  { label: '取得借款', value: 'fin_borrow' },
  { label: '偿还债务', value: 'fin_repay' },
  { label: '分配股利', value: 'fin_dividend' },
]

const DIRECTION_OPTIONS = [
  { label: '流入 (inflow)', value: 'inflow' },
  { label: '流出 (outflow)', value: 'outflow' },
]

function getCategoryLabel(code: string) {
  const opt = CATEGORY_OPTIONS.find(o => o.value === code)
  return opt ? opt.label : code
}

async function loadItems() {
  loading.value = true
  try {
    const cid = Number(JSON.parse(localStorage.getItem('user') || '{}').company_id || 1)
    const res = await listCashFlowItems(cid)
    items.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    toast.add({ severity: 'error', summary: '加载失败', detail: String(e), life: 4000 })
  } finally {
    loading.value = false
  }
}

function openAdd() {
  isEdit.value = false
  editId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(item: any) {
  isEdit.value = true
  editId.value = item.id
  form.value = {
    code: item.code,
    name: item.name,
    category_code: item.category_code || '',
    direction: item.direction || 'inflow',
    debit_accounts: item.debit_accounts || '',
    credit_accounts: item.credit_accounts || '',
    is_active: item.is_active,
  }
  showDialog.value = true
}

async function handleSave() {
  try {
    const cid = Number(JSON.parse(localStorage.getItem('user') || '{}').company_id || 1)
    if (isEdit.value && editId.value) {
      await updateCashFlowItem(editId.value, form.value)
      toast.add({ severity: 'success', summary: '已更新', life: 2000 })
    } else {
      await createCashFlowItem({ ...form.value, company_id: cid })
      toast.add({ severity: 'success', summary: '已创建', life: 2000 })
    }
    showDialog.value = false
    await loadItems()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '保存失败', detail: e?.response?.data?.detail || String(e), life: 4000 })
  }
}

async function handleDelete(item: any) {
  if (!confirm(`确认删除 "${item.name}"？`)) return
  try {
    await deleteCashFlowItem(item.id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await loadItems()
  } catch (e) {
    toast.add({ severity: 'error', summary: '删除失败', detail: String(e), life: 4000 })
  }
}

async function handleSeedDefaults() {
  if (!confirm('将用国标预设项目重置当前公司的现金流量映射，确认？')) return
  try {
    const cid = Number(JSON.parse(localStorage.getItem('user') || '{}').company_id || 1)
    await seedDefaultCashFlowItems(cid)
    toast.add({ severity: 'success', summary: '已补齐国标预设', life: 2000 })
    await loadItems()
  } catch (e) {
    toast.add({ severity: 'error', summary: '操作失败', detail: String(e), life: 4000 })
  }
}

onMounted(() => loadItems())
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-zinc-800">现金流量表项目映射</h2>
      <div class="flex gap-2">
        <Button
          label="补齐国标预设"
          icon="pi pi-refresh"
          severity="secondary"
          size="small"
          @click="handleSeedDefaults"
        />
        <Button label="新增项目" icon="pi pi-plus" size="small" @click="openAdd" />
      </div>
    </div>

    <div class="bg-white rounded-sm border border-zinc-200 shadow-sm">
      <DataTable :value="items" :loading="loading" stripedRows size="small" tableStyle="min-width: auto">
        <Column field="code" header="编码" style="width: 80px" />
        <Column field="name" header="项目名称" style="width: 260px" />
        <Column header="报表位置" style="width: 150px">
          <template #body="{ data }">{{ getCategoryLabel(data.category_code) }}</template>
        </Column>
        <Column header="方向" style="width: 70px">
          <template #body="{ data }">
            <span :class="data.direction === 'inflow' ? 'text-green-600' : 'text-red-600'">
              {{ data.direction === 'inflow' ? '流入' : '流出' }}
            </span>
          </template>
        </Column>
        <Column field="debit_accounts" header="借方对方科目" style="width: 200px">
          <template #body="{ data }">
            <code class="text-xs bg-zinc-100 px-1 rounded">{{ data.debit_accounts || '-' }}</code>
          </template>
        </Column>
        <Column field="credit_accounts" header="贷方对方科目" style="width: 200px">
          <template #body="{ data }">
            <code class="text-xs bg-zinc-100 px-1 rounded">{{ data.credit_accounts || '-' }}</code>
          </template>
        </Column>
        <Column header="启用" style="width: 60px">
          <template #body="{ data }">
            <i :class="data.is_active ? 'pi pi-check text-green-500' : 'pi pi-times text-red-400'" />
          </template>
        </Column>
        <Column header="操作" style="width: 120px">
          <template #body="{ data }">
            <Button icon="pi pi-pencil" severity="secondary" text size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" severity="danger" text size="small" @click="handleDelete(data)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Edit / Add Dialog -->
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑现金流量项目' : '新增现金流量项目'"
      :modal="true"
      class="w-[520px]"
    >
      <div class="flex flex-col gap-3 pt-2">
        <div class="flex gap-3">
          <div class="flex-1">
            <label class="block text-sm text-zinc-600 mb-1">编码</label>
            <InputText v-model="form.code" class="w-full" :disabled="isEdit" />
          </div>
          <div>
            <label class="block text-sm text-zinc-600 mb-1">方向</label>
            <Dropdown
              v-model="form.direction"
              :options="DIRECTION_OPTIONS"
              optionLabel="label"
              optionValue="value"
              class="w-32"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm text-zinc-600 mb-1">项目名称</label>
          <InputText v-model="form.name" class="w-full" />
        </div>

        <div>
          <label class="block text-sm text-zinc-600 mb-1">映射到报表行</label>
          <Dropdown
            v-model="form.category_code"
            :options="CATEGORY_OPTIONS"
            optionLabel="label"
            optionValue="value"
            class="w-full"
            showClear
            placeholder="选择报表行..."
          />
        </div>

        <div>
          <label class="block text-sm text-zinc-600 mb-1">
            借方对方科目
            <span class="text-zinc-400">（现金流出时，对方借方的科目范围）</span>
          </label>
          <InputText v-model="form.debit_accounts" class="w-full" placeholder="如: 2211,2221,6602" />
        </div>

        <div>
          <label class="block text-sm text-zinc-600 mb-1">
            贷方对方科目
            <span class="text-zinc-400">（现金流入时，对方贷方的科目范围）</span>
          </label>
          <InputText v-model="form.credit_accounts" class="w-full" placeholder="如: 1122,6001,2241" />
        </div>

        <div class="flex items-center gap-2">
          <ToggleSwitch v-model="form.is_active" />
          <span class="text-sm text-zinc-600">启用该项目</span>
        </div>
      </div>

      <template #footer>
        <Button label="取消" severity="secondary" @click="showDialog = false" />
        <Button label="保存" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
