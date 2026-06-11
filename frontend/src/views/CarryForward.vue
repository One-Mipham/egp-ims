<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import {
  listCarryForwards, createCarryForward, executeCarryForward, deleteCarryForward,
} from '@/api'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)

const entryTypes = [
  { label: '收入结转至本年利润', value: 'revenue_to_profit' },
  { label: '费用结转至本年利润', value: 'expense_to_profit' },
  { label: '本年利润结转至未分配利润', value: 'profit_to_retained' },
]
const typeLabels: Record<string, string> = {
  revenue_to_profit: '收入→利润',
  expense_to_profit: '费用→利润',
  profit_to_retained: '利润→留存',
}

const emptyForm = () => ({
  company_id: companyId.value,
  period: new Date().toISOString().slice(0, 7),  // yyyy-MM
  entry_type: 'revenue_to_profit',
  debit_account_id: undefined as number | undefined,
  credit_account_id: undefined as number | undefined,
  amount: 0,
})
const form = ref(emptyForm())
const amountInput = ref('0')

async function load() {
  loading.value = true
  try {
    const res = await listCarryForwards(companyId.value)
    items.value = res.data
  } finally { loading.value = false }
}

function openAdd() {
  form.value = emptyForm()
  amountInput.value = '0'
  showDialog.value = true
}

async function handleSave() {
  const amount = parseFloat(amountInput.value) || 0
  if (!form.value.period || !amount) return
  try {
    await createCarryForward({ ...form.value, amount })
    showDialog.value = false
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '保存失败') }
}

async function handleExecute(id: number) {
  if (!confirm('确认执行此结转？')) return
  try {
    await executeCarryForward(id)
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '执行失败') }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除？')) return
  try {
    await deleteCarryForward(id)
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '删除失败') }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">期末结转</h2>
      <Button label="新增结转" icon="pi pi-plus" @click="openAdd" />
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows paginator :rows="15" class="shadow-sm">
        <Column header="序号" style="width:60px">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column field="period" header="期间" style="width:100px" />
        <Column header="结转类型" style="width:130px">
          <template #body="{ data }">{{ typeLabels[data.entry_type] || data.entry_type }}</template>
        </Column>
        <Column field="amount" header="金额" style="width:120px">
          <template #body="{ data }">¥{{ Number(data.amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="status" header="状态" style="width:80px">
          <template #body="{ data }">
            <Tag :value="data.status === 'executed' ? '已执行' : '草稿'"
              :severity="data.status === 'executed' ? 'success' : 'warning'" />
          </template>
        </Column>
        <Column header="执行时间" style="width:150px">
          <template #body="{ data }">{{ data.executed_at?.slice(0, 10) || '-' }}</template>
        </Column>
        <Column header="操作" style="width:150px">
          <template #body="{ data }">
            <Button v-if="data.status !== 'executed'" label="执行" text severity="success"
              size="small" @click="handleExecute(data.id)" />
            <Button v-if="data.status !== 'executed'" label="删除" text severity="danger"
              size="small" @click="handleDelete(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showDialog" header="新增结转" :style="{ width: '500px' }" :modal="true">
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">期间 (yyyy-MM)</label>
            <InputText v-model="form.period" class="w-full" placeholder="2026-05" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">结转类型</label>
            <Select v-model="form.entry_type" :options="entryTypes"
              optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">金额 *</label>
            <InputText v-model="amountInput" class="w-full" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showDialog = false" />
        <Button label="保存" icon="pi pi-check" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
