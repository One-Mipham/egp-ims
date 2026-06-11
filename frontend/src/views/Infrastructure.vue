<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'; import Column from 'primevue/column'
import Button from 'primevue/button'; import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'; import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'; import Tag from 'primevue/tag'
import api from '@/api/index'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false); const isEdit = ref(false); const editId = ref<number | null>(null)
const filterType = ref<string | null>(null)

const INFRA_TYPES = [{ label: '能源 Energy', value: 'energy' }, { label: '交通 Transport', value: 'transport' }, { label: '公用事业 Utilities', value: 'utilities' }, { label: '通信 Telecom', value: 'telecom' }, { label: '社会基础设施 Social', value: 'social' }, { label: 'PPP', value: 'ppp' }]
const TYPE_LABELS = Object.fromEntries(INFRA_TYPES.map(t => [t.value, t.label]))
const STATUS_LABELS: Record<string, string> = { development: '开发中', operational: '运营中', harvesting: '收获期', sold: '已出售' }

const emptyForm = () => ({ project_name: '', asset_type: 'energy', location: '', investment_date: '', investment_amount: 0, current_value: 0, valuation_date: '', annual_revenue: 0, concession_expiry: '', portfolio_id: null as number | null })
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try { const r = await api.get('/investments/infrastructure', { params: { company_id: companyId.value, ...(filterType.value ? { asset_type: filterType.value } : {}) } }); items.value = r.data }
  finally { loading.value = false }
}

function openAdd() { form.value = emptyForm(); isEdit.value = false; editId.value = null; showDialog.value = true }
function openEdit(row: any) { form.value = { ...row }; isEdit.value = true; editId.value = row.id; showDialog.value = true }
async function handleSave() {
  if (!form.value.project_name) return
  if (isEdit.value && editId.value) { await api.put(`/investments/infrastructure/${editId.value}`, form.value) }
  else { await api.post('/investments/infrastructure', form.value, { params: { company_id: companyId.value } }) }
  showDialog.value = false; await load()
}
async function handleDelete(id: number) { if (!confirm('确定删除？')) return; await api.delete(`/investments/infrastructure/${id}`); await load() }

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">基础设施资产</h2>
      <Button label="新增项目" icon="pi pi-plus" size="small" @click="openAdd" />
    </div>

    <div class="flex gap-3 mb-3">
      <Dropdown v-model="filterType" :options="INFRA_TYPES" optionLabel="label" optionValue="value" placeholder="全部类型" showClear class="w-48" @change="load" />
    </div>

    <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="project_name" header="项目名称" sortable />
      <Column header="类型"><template #body="{ data }"><Tag :value="TYPE_LABELS[data.asset_type] || data.asset_type" severity="info" /></template></Column>
      <Column field="location" header="位置" />
      <Column header="投资额"><template #body="{ data }">¥{{ data.investment_amount?.toLocaleString() }}</template></Column>
      <Column header="当前估值"><template #body="{ data }">¥{{ data.current_value?.toLocaleString() }}</template></Column>
      <Column header="年运营收入"><template #body="{ data }">¥{{ data.annual_revenue?.toLocaleString() }}</template></Column>
      <Column field="concession_expiry" header="特许到期" />
      <Column header="状态"><template #body="{ data }"><Tag :value="STATUS_LABELS[data.status] || data.status" :severity="data.status === 'operational' ? 'success' : data.status === 'development' ? 'warn' : 'info'" /></template></Column>
      <Column header="操作" style="width:100px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" size="small" severity="secondary" text rounded @click="openEdit(data)" />
            <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑项目' : '新增项目'" :style="{ width: '520px' }" modal>
      <div class="flex flex-col gap-3 pt-2">
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-sm text-stone-600">项目名称 *</label><InputText v-model="form.project_name" class="w-full" /></div>
          <div><label class="text-sm text-stone-600">类型</label><Dropdown v-model="form.asset_type" :options="INFRA_TYPES" optionLabel="label" optionValue="value" class="w-full" /></div>
        </div>
        <div><label class="text-sm text-stone-600">位置</label><InputText v-model="form.location" class="w-full" /></div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-sm text-stone-600">投资日期</label><InputText v-model="form.investment_date" class="w-full" placeholder="YYYY-MM-DD" /></div>
          <div><label class="text-sm text-stone-600">投资额</label><InputNumber v-model="form.investment_amount" mode="currency" currency="CNY" class="w-full" /></div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-sm text-stone-600">当前估值</label><InputNumber v-model="form.current_value" mode="currency" currency="CNY" class="w-full" /></div>
          <div><label class="text-sm text-stone-600">估值日期</label><InputText v-model="form.valuation_date" class="w-full" placeholder="YYYY-MM-DD" /></div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-sm text-stone-600">年运营收入</label><InputNumber v-model="form.annual_revenue" mode="currency" currency="CNY" class="w-full" /></div>
          <div><label class="text-sm text-stone-600">特许经营到期</label><InputText v-model="form.concession_expiry" class="w-full" placeholder="YYYY-MM-DD" /></div>
        </div>
      </div>
      <template #footer><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="handleSave" :disabled="!form.project_name" /></template>
    </Dialog>
  </div>
</template>
