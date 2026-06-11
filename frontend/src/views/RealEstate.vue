<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'; import Column from 'primevue/column'
import Button from 'primevue/button'; import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'; import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'; import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import api from '@/api/index'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false); const isEdit = ref(false); const editId = ref<number | null>(null)
const filterType = ref<string | null>(null)

const PROP_TYPES = [{ label: '商业 Commercial', value: 'commercial' }, { label: '住宅 Residential', value: 'residential' }, { label: '工业 Industrial', value: 'industrial' }, { label: '土地 Land', value: 'land' }, { label: '混合 Mixed', value: 'mixed' }]
const TYPE_LABELS = Object.fromEntries(PROP_TYPES.map(t => [t.value, t.label]))
const STATUS_LABELS: Record<string, string> = { active: '持有', sold: '已出售', under_renovation: '装修中' }

const emptyForm = () => ({ property_name: '', property_type: 'commercial', location: '', acquisition_date: '', acquisition_cost: 0, current_value: 0, valuation_date: '', area_sqm: 0, occupancy_pct: 0, annual_rental_income: 0, portfolio_id: null as number | null })
const form = ref(emptyForm())

// Valuation sub-component
const selectedAsset = ref<any>(null); const showValDialog = ref(false)
const valForm = ref({ valuation_date: '', value: 0, valuation_method: 'comparable', appraiser: '', notes: '' })
const valuations = ref<any[]>([])
const valMethods = [{ label: '可比法', value: 'comparable' }, { label: '成本法', value: 'cost' }, { label: '收益法', value: 'income' }, { label: 'DCF', value: 'dcf' }]

async function load() {
  loading.value = true
  try { const r = await api.get('/investments/real-estate', { params: { company_id: companyId.value, ...(filterType.value ? { property_type: filterType.value } : {}) } }); items.value = r.data }
  finally { loading.value = false }
}

function openAdd() { form.value = emptyForm(); isEdit.value = false; editId.value = null; showDialog.value = true }
function openEdit(row: any) { form.value = { ...row }; isEdit.value = true; editId.value = row.id; showDialog.value = true }
async function handleSave() {
  if (!form.value.property_name) return
  if (isEdit.value && editId.value) { await api.put(`/investments/real-estate/${editId.value}`, form.value) }
  else { await api.post('/investments/real-estate', form.value, { params: { company_id: companyId.value } }) }
  showDialog.value = false; await load()
}
async function handleDelete(id: number) { if (!confirm('确定删除？')) return; await api.delete(`/investments/real-estate/${id}`); await load() }

// Valuations
async function openValuations(row: any) {
  selectedAsset.value = row
  try { const r = await api.get(`/investments/real-estate/${row.id}/valuations`); valuations.value = r.data } catch { valuations.value = [] }
  showValDialog.value = true
}
async function saveValuation() {
  if (!valForm.value.valuation_date) return
  await api.post(`/investments/real-estate/${selectedAsset.value.id}/valuations`, valForm.value, { params: { company_id: companyId.value } })
  try { const r = await api.get(`/investments/real-estate/${selectedAsset.value.id}/valuations`); valuations.value = r.data } catch {}
  valForm.value = { valuation_date: '', value: 0, valuation_method: 'comparable', appraiser: '', notes: '' }
}
async function deleteValuation(valId: number) {
  if (!confirm('确定删除？')) return
  await api.delete(`/investments/real-estate/${selectedAsset.value.id}/valuations/${valId}`)
  try { const r = await api.get(`/investments/real-estate/${selectedAsset.value.id}/valuations`); valuations.value = r.data } catch {}
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">房地产资产</h2>
      <Button label="新增资产" icon="pi pi-plus" size="small" @click="openAdd" />
    </div>

    <div class="flex gap-3 mb-3">
      <Dropdown v-model="filterType" :options="PROP_TYPES" optionLabel="label" optionValue="value" placeholder="全部类型" showClear class="w-48" @change="load" />
    </div>

    <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="property_name" header="资产名称" sortable />
      <Column header="类型"><template #body="{ data }"><Tag :value="TYPE_LABELS[data.property_type] || data.property_type" severity="info" /></template></Column>
      <Column field="location" header="位置" />
      <Column header="收购成本"><template #body="{ data }">¥{{ data.acquisition_cost?.toLocaleString() }}</template></Column>
      <Column header="当前估值"><template #body="{ data }">¥{{ data.current_value?.toLocaleString() }}</template></Column>
      <Column header="出租率"><template #body="{ data }">{{ data.occupancy_pct ? data.occupancy_pct + '%' : '-' }}</template></Column>
      <Column header="年租金"><template #body="{ data }">¥{{ data.annual_rental_income?.toLocaleString() }}</template></Column>
      <Column header="状态"><template #body="{ data }"><Tag :value="STATUS_LABELS[data.status] || data.status" :severity="data.status === 'active' ? 'success' : 'danger'" /></template></Column>
      <Column header="操作" style="width:140px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-chart-line" size="small" severity="info" text rounded @click="openValuations(data)" title="估值记录" />
            <Button icon="pi pi-pencil" size="small" severity="secondary" text rounded @click="openEdit(data)" />
            <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Asset Dialog -->
    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑资产' : '新增资产'" :style="{ width: '520px' }" modal>
      <div class="flex flex-col gap-3 pt-2">
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-sm text-stone-600">名称 *</label><InputText v-model="form.property_name" class="w-full" /></div>
          <div><label class="text-sm text-stone-600">类型</label><Dropdown v-model="form.property_type" :options="PROP_TYPES" optionLabel="label" optionValue="value" class="w-full" /></div>
        </div>
        <div><label class="text-sm text-stone-600">位置</label><InputText v-model="form.location" class="w-full" /></div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-sm text-stone-600">收购日期</label><InputText v-model="form.acquisition_date" class="w-full" placeholder="YYYY-MM-DD" /></div>
          <div><label class="text-sm text-stone-600">收购成本</label><InputNumber v-model="form.acquisition_cost" mode="currency" currency="CNY" class="w-full" /></div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div><label class="text-sm text-stone-600">建筑面积(m²)</label><InputNumber v-model="form.area_sqm" class="w-full" /></div>
          <div><label class="text-sm text-stone-600">出租率%</label><InputNumber v-model="form.occupancy_pct" suffix="%" class="w-full" /></div>
          <div><label class="text-sm text-stone-600">年租金</label><InputNumber v-model="form.annual_rental_income" mode="currency" currency="CNY" class="w-full" /></div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-sm text-stone-600">当前估值</label><InputNumber v-model="form.current_value" mode="currency" currency="CNY" class="w-full" /></div>
          <div><label class="text-sm text-stone-600">估值日期</label><InputText v-model="form.valuation_date" class="w-full" placeholder="YYYY-MM-DD" /></div>
        </div>
      </div>
      <template #footer><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="handleSave" :disabled="!form.property_name" /></template>
    </Dialog>

    <!-- Valuations Dialog -->
    <Dialog v-model:visible="showValDialog" :header="'估值历史: ' + (selectedAsset?.property_name || '')" :style="{ width: '600px' }" modal>
      <div class="flex gap-2 mb-3">
        <InputText v-model="valForm.valuation_date" placeholder="日期" class="w-28" />
        <InputNumber v-model="valForm.value" mode="currency" currency="CNY" class="w-36" />
        <Dropdown v-model="valForm.valuation_method" :options="valMethods" optionLabel="label" optionValue="value" class="w-28" />
        <InputText v-model="valForm.appraiser" placeholder="评估机构" class="w-32" />
        <InputText v-model="valForm.notes" placeholder="备注" class="w-24" />
        <Button icon="pi pi-plus" size="small" @click="saveValuation" :disabled="!valForm.valuation_date" />
      </div>
      <DataTable :value="valuations" stripedRows size="small">
        <Column field="valuation_date" header="日期" />
        <Column header="估值"><template #body="{ data }">¥{{ data.value?.toLocaleString() }}</template></Column>
        <Column field="valuation_method" header="方法" />
        <Column field="appraiser" header="评估机构" />
        <Column field="notes" header="备注" />
        <Column header="" style="width:50px">
          <template #body="{ data }"><Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="deleteValuation(data.id)" /></template>
        </Column>
      </DataTable>
    </Dialog>
  </div>
</template>
