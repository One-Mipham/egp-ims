<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import { listCounterparties, listDepartments } from '@/api'
import api from '@/api'

const invoices = ref<any[]>([])
const counterparties = ref<any[]>([])
const departments = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const searchKeyword = ref('')
const filterDepartment = ref<number | null>(null)
const filterCustomer = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const INVOICE_TYPES = [
  { label: '增值税专用发票', value: 'vat_special' },
  { label: '增值税普通发票', value: 'vat_normal' },
  { label: '电子发票', value: 'electronic' },
]

const TYPE_LABELS: Record<string, string> = {
  vat_special: '专票', vat_normal: '普票', electronic: '电子',
}

const emptyForm = () => ({
  invoice_no: '', invoice_type: 'vat_special', counterparty_id: null as number | null,
  department_id: null as number | null,
  amount: 0, invoice_date: '', notes: '',
})
const form = ref(emptyForm())

const filteredInvoices = computed(() => {
  let result = invoices.value
  if (searchKeyword.value) {
    const q = searchKeyword.value.toLowerCase()
    result = result.filter((i: any) =>
      (i.invoice_no || '').includes(q) || (i.notes || '').includes(q)
    )
  }
  if (filterDepartment.value) {
    result = result.filter((i: any) => i.department_id === filterDepartment.value)
  }
  if (filterCustomer.value) {
    result = result.filter((i: any) => i.counterparty_id === filterCustomer.value)
  }
  return result
})

async function load() {
  loading.value = true
  try {
    const [iRes, cpRes, dRes] = await Promise.all([
      api.get('/investments/init/invoices', { params: { company_id: companyId.value } }),
      listCounterparties(companyId.value),
      listDepartments(companyId.value),
    ])
    invoices.value = iRes.data
    counterparties.value = cpRes.data
    departments.value = dRes.data
  } catch { /* API may not exist yet */ }
  finally { loading.value = false }
}

function getCustomerName(id: number | null) {
  if (!id) return ''
  const cp = counterparties.value.find((c: any) => c.id === id)
  return cp ? cp.name : ''
}

function getDepartmentName(id: number | null) {
  if (!id) return ''
  const d = departments.value.find((d: any) => d.id === id)
  return d ? d.name : ''
}

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    invoice_no: row.invoice_no, invoice_type: row.invoice_type,
    counterparty_id: row.counterparty_id, department_id: row.department_id,
    amount: row.amount, invoice_date: row.invoice_date || '', notes: row.notes || '',
  }
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.invoice_no) return
  saving.value = true
  try {
    if (editingId.value) {
      await api.put(`/investments/init/invoices/${editingId.value}`, form.value)
    } else {
      await api.post('/investments/init/invoices', form.value, { params: { company_id: companyId.value } })
    }
    showDialog.value = false
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除该发票？')) return
  try {
    await api.delete(`/investments/init/invoices/${id}`)
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '删除失败') }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-2">
      <h2 class="text-lg font-semibold text-zinc-700">业务发票</h2>
      <div class="flex gap-2">
        <Button label="导入" icon="pi pi-upload" outlined size="small" />
        <Button label="新增发票" icon="pi pi-plus" @click="openAdd" size="small" />
      </div>
    </div>

    <!-- Search filters -->
    <div class="flex gap-2 items-center mb-3 flex-wrap">
      <InputText v-model="searchKeyword" placeholder="发票号码/关键字..." class="w-64" />
      <Dropdown v-model="filterDepartment" :options="departments" optionLabel="name" optionValue="id"
                placeholder="经办部门" class="w-36" showClear />
      <Dropdown v-model="filterCustomer" :options="counterparties" optionLabel="name" optionValue="id"
                placeholder="客户名称" class="w-40" showClear filter />
    </div>

    <DataTable :value="filteredInvoices" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="invoice_no" header="发票号码" sortable style="width:150px" />
      <Column field="invoice_type" header="发票类型" sortable style="width:80px">
        <template #body="{ data }">
          <Tag :value="TYPE_LABELS[data.invoice_type] || data.invoice_type"
               :severity="data.invoice_type === 'vat_special' ? 'info' : 'success'" />
        </template>
      </Column>
      <Column header="客户名称" sortable style="width:150px">
        <template #body="{ data }">{{ getCustomerName(data.counterparty_id) }}</template>
      </Column>
      <Column header="经办部门" sortable style="width:100px">
        <template #body="{ data }">{{ getDepartmentName(data.department_id) }}</template>
      </Column>
      <Column field="amount" header="金额" sortable style="width:120px">
        <template #body="{ data }">{{ data.amount.toLocaleString() }}</template>
      </Column>
      <Column field="invoice_date" header="开票日期" sortable style="width:100px" />
      <Column field="notes" header="备注" />
      <Column header="操作" style="width:140px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" text size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑发票' : '新增发票'" :modal="true" class="w-[550px]">
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">发票号码 *</label>
            <InputText v-model="form.invoice_no" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">发票类型</label>
            <Dropdown v-model="form.invoice_type" :options="INVOICE_TYPES" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">客户名称</label>
            <Dropdown v-model="form.counterparty_id" :options="counterparties" optionLabel="name" optionValue="id"
                      class="w-full" showClear filter />
          </div>
          <div>
            <label class="block text-sm mb-1">经办部门</label>
            <Dropdown v-model="form.department_id" :options="departments" optionLabel="name" optionValue="id"
                      class="w-full" showClear />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">金额</label>
            <InputNumber v-model="form.amount" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">开票日期</label>
            <InputText v-model="form.invoice_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
        </div>
        <div>
          <label class="block text-sm mb-1">备注</label>
          <Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" text @click="showDialog = false" />
        <Button label="保存" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
