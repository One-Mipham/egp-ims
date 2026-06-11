<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Calendar from 'primevue/calendar'
import {
  listInvoices, createInvoice, updateInvoice, deleteInvoice,
} from '@/api/taxes'
import { listCounterparties } from '@/api'

const route = useRoute()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const mode = computed(() => {
  const p = route.path
  if (p.includes('/sales')) return 'sales'
  if (p.includes('/purchase')) return 'purchase'
  return 'query'
})

const modeLabel = computed(() => {
  if (mode.value === 'sales') return '销项发票'
  if (mode.value === 'purchase') return '进项发票'
  return '发票查询统计'
})

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const search = ref('')
const dateFrom = ref<Date | null>(null)
const dateTo = ref<Date | null>(null)
const counterparties = ref<any[]>([])

const statusLabels: Record<string, string> = { draft: '草稿', issued: '已开票', verified: '已核验' }

const emptyForm = () => ({
  company_id: companyId.value,
  invoice_type: mode.value === 'sales' ? 'sales' : 'purchase',
  invoice_number: '',
  invoice_date: new Date() as Date | null,
  counterparty_id: null as number | null,
  amount: 0,
  tax_rate: 13,
  tax_amount: 0,
  total_amount: 0,
  category: '',
  status: 'draft',
  notes: '',
})
const form = ref(emptyForm())

watch(() => [form.value.amount, form.value.tax_rate], () => {
  const amt = Number(form.value.amount) || 0
  const rate = Number(form.value.tax_rate) || 0
  form.value.tax_amount = Math.round(amt * rate) / 100
  form.value.total_amount = amt + form.value.tax_amount
})

function fmtDate(d: Date | null): string | undefined {
  if (!d) return undefined
  return d.toISOString().slice(0, 10)
}

function getFilters() {
  const params: any = { company_id: companyId.value }
  if (mode.value === 'sales') params.invoice_type = 'sales'
  if (mode.value === 'purchase') params.invoice_type = 'purchase'
  if (dateFrom.value) params.date_from = fmtDate(dateFrom.value)
  if (dateTo.value) params.date_to = fmtDate(dateTo.value)
  return params
}

async function load() {
  loading.value = true
  try {
    const res = await listInvoices(getFilters())
    items.value = res.data
  } finally { loading.value = false }
}

async function loadCounterparties() {
  try {
    const res = await listCounterparties(companyId.value)
    counterparties.value = res.data
  } catch {}
}

const filteredItems = computed(() => {
  if (!search.value) return items.value
  const q = search.value.toLowerCase()
  return items.value.filter((i: any) =>
    (i.invoice_number || '').toLowerCase().includes(q) ||
    (i.category || '').toLowerCase().includes(q)
  )
})

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  if (mode.value === 'query') form.value.invoice_type = 'sales'
  loadCounterparties()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    company_id: row.company_id,
    invoice_type: row.invoice_type,
    invoice_number: row.invoice_number,
    invoice_date: row.invoice_date ? new Date(row.invoice_date) : null,
    counterparty_id: row.counterparty_id,
    amount: row.amount,
    tax_rate: row.tax_rate,
    tax_amount: row.tax_amount,
    total_amount: row.total_amount,
    category: row.category || '',
    status: row.status,
    notes: row.notes || '',
  }
  loadCounterparties()
  showDialog.value = true
}

function buildPayload() {
  return {
    ...form.value,
    invoice_date: fmtDate(form.value.invoice_date),
  }
}

async function handleSave() {
  if (!form.value.invoice_number) return
  try {
    const payload = buildPayload()
    if (editingId.value) {
      await updateInvoice(editingId.value, payload)
    } else {
      await createInvoice(payload)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除该发票记录？')) return
  try {
    await deleteInvoice(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function getCounterpartyName(id: number | null) {
  if (!id) return ''
  const cp = counterparties.value.find((c: any) => c.id === id)
  return cp?.name || ''
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">{{ modeLabel }}</h2>
      <div class="flex gap-2">
        <InputText v-model="search" placeholder="搜索发票号/类别..." class="w-56" />
        <Calendar v-model="dateFrom" placeholder="起始日期" showIcon class="w-36" @value-change="load" />
        <Calendar v-model="dateTo" placeholder="截止日期" showIcon class="w-36" @value-change="load" />
        <Button label="查询" icon="pi pi-search" severity="secondary" @click="load" />
        <Button v-if="mode !== 'query'" label="新增" icon="pi pi-plus" @click="openAdd" />
      </div>
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="filteredItems" :loading="loading" stripedRows paginator :rows="15" class="shadow-sm">
        <Column header="序号" style="width:60px">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column field="invoice_number" header="发票号码" style="width:150px" />
        <Column field="invoice_date" header="开票日期" style="width:110px">
          <template #body="{ data }">{{ data.invoice_date?.slice(0, 10) }}</template>
        </Column>
        <Column v-if="mode === 'query'" field="invoice_type" header="类型" style="width:80px">
          <template #body="{ data }">{{ data.invoice_type === 'sales' ? '销项' : '进项' }}</template>
        </Column>
        <Column header="对方单位" style="width:160px">
          <template #body="{ data }">{{ getCounterpartyName(data.counterparty_id) || '-' }}</template>
        </Column>
        <Column field="amount" header="金额（不含税）" style="width:130px">
          <template #body="{ data }">¥{{ Number(data.amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="tax_rate" header="税率" style="width:70px">
          <template #body="{ data }">{{ data.tax_rate }}%</template>
        </Column>
        <Column field="tax_amount" header="税额" style="width:110px">
          <template #body="{ data }">¥{{ Number(data.tax_amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="total_amount" header="价税合计" style="width:130px">
          <template #body="{ data }">¥{{ Number(data.total_amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="category" header="类别" style="width:90px" />
        <Column field="status" header="状态" style="width:80px">
          <template #body="{ data }">{{ statusLabels[data.status] || data.status }}</template>
        </Column>
        <Column header="操作" style="width:130px">
          <template #body="{ data }">
            <Button label="编辑" text severity="info" size="small" @click="openEdit(data)" />
            <Button label="删除" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑发票' : '新增发票'" :style="{ width: '780px' }">
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">发票类型</label>
            <Select v-model="form.invoice_type" :options="[
              { label: '销项发票', value: 'sales' },
              { label: '进项发票', value: 'purchase' },
            ]" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">发票号码 *</label>
            <InputText v-model="form.invoice_number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">开票日期</label>
            <Calendar v-model="form.invoice_date" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">对方单位</label>
            <Select v-model="form.counterparty_id" :options="counterparties"
              optionLabel="name" optionValue="id" showClear filter
              placeholder="选择往来单位" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">商品/服务类别</label>
            <InputText v-model="form.category" class="w-full" placeholder="如：咨询/软件/货物" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">金额（不含税）</label>
            <input type="number" v-model.number="form.amount" class="w-full border border-stone-300 rounded px-3 py-2 text-sm" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税率（%）</label>
            <input type="number" v-model.number="form.tax_rate" class="w-full border border-stone-300 rounded px-3 py-2 text-sm" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税额（自动）</label>
            <input :value="form.tax_amount" disabled class="w-full border border-stone-200 rounded px-3 py-2 text-sm bg-stone-50" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">价税合计（自动）</label>
            <input :value="form.total_amount" disabled class="w-full border border-stone-200 rounded px-3 py-2 text-sm bg-stone-50" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">状态</label>
            <Select v-model="form.status" :options="[
              { label: '草稿', value: 'draft' },
              { label: '已开票', value: 'issued' },
              { label: '已核验', value: 'verified' },
            ]" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="flex-[2]">
            <label class="block text-xs text-zinc-500 mb-1">备注</label>
            <InputText v-model="form.notes" class="w-full" />
          </div>
        </div>
        <div>
          <Button label="保存" icon="pi pi-check" @click="handleSave" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
