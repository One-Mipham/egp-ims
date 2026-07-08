<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import {
  listInsurance,
  createInsurance,
  updateInsurance,
  deleteInsurance,
  submitInsurance,
  listExpiringInsurance,
} from '@/api'

const items = ref<any[]>([])
const expiring = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = ref(1)
const policyTypes = ['财产险', '综合险', '责任险', '其他']
const emptyForm = () => ({
  company_id: companyId.value,
  policy_type: '财产险',
  insured_assets: '',
  insurance_company: '',
  coverage_amount: 0,
  premium: 0,
  start_date: '',
  end_date: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [r1, r2] = await Promise.all([listInsurance(companyId.value), listExpiringInsurance(companyId.value, 30)])
    items.value = r1.data
    expiring.value = r2.data
  } finally {
    loading.value = false
  }
}
function openCreate() {
  form.value = emptyForm()
  isEdit.value = false
  showDialog.value = true
}
function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true
  editId.value = row.id
  showDialog.value = true
}
async function save() {
  try {
    if (isEdit.value && editId.value) await updateInsurance(editId.value, form.value)
    else await createInsurance(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}
async function remove(id: number) {
  if (!confirm('确定删除？')) return
  try {
    await deleteInsurance(id)
    await load()
  } catch (_e: any) {
    alert('删除失败')
  }
}
async function doSubmit(id: number) {
  const ids = prompt('请输入审批人ID（逗号分隔）：')
  if (!ids) return
  try {
    await submitInsurance(id, ids.split(',').map(Number))
    await load()
  } catch (_e: any) {
    alert('提交失败')
  }
}
const statusSeverity = (s: string) =>
  (({ draft: 'secondary', pending_approval: 'warn', active: 'success', expired: 'danger', rejected: 'danger' }) as any)[
    s
  ] || 'secondary'
onMounted(load)
</script>

<template>
  <div>
    <div v-if="expiring.length" class="bg-orange-50 border border-orange-200 rounded-sm p-3 mb-4">
      <h3 class="text-sm font-semibold text-orange-700 mb-2">即将到期保单（30天内）</h3>
      <div v-for="p in expiring" :key="p.id" class="text-sm text-orange-600">
        「{{ p.insured_assets }}」— {{ p.insurance_company }}，到期日：{{ p.end_date }}
      </div>
    </div>
    <div class="flex justify-end mb-4"><Button label="新建保单" icon="pi pi-plus" @click="openCreate" /></div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="insured_assets" header="投保资产" sortable />
        <Column field="policy_type" header="险种" sortable />
        <Column field="insurance_company" header="保险公司" sortable />
        <Column field="coverage_amount" header="保额" sortable />
        <Column field="premium" header="保费" sortable />
        <Column field="start_date" header="起期" sortable style="min-width: 90px" />
        <Column field="end_date" header="止期" sortable style="min-width: 90px" />
        <Column header="状态" style="min-width: 80px">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column header="操作" style="min-width: 160px">
          <template #body="{ data }">
            <Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" />
            <Button v-if="data.status === 'draft'" text size="small" icon="pi pi-send" @click="doSubmit(data.id)" />
            <Button
              v-if="data.status === 'draft'"
              text
              size="small"
              icon="pi pi-trash"
              severity="danger"
              @click="remove(data.id)"
            />
          </template>
        </Column>
      </DataTable>
    </div>
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑保单' : '新建保单'"
      :style="{ width: '550px' }"
      :modal="true"
    >
      <div class="grid grid-cols-2 gap-3">
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">投保资产</label
          ><InputText v-model="form.insured_assets" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">险种</label
          ><Dropdown v-model="form.policy_type" :options="policyTypes" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">保险公司</label
          ><InputText v-model="form.insurance_company" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">保额</label
          ><InputNumber v-model="form.coverage_amount" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">保费</label
          ><InputNumber v-model="form.premium" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">起期</label
          ><InputText v-model="form.start_date" type="date" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">止期</label
          ><InputText v-model="form.end_date" type="date" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="save"
      /></template>
    </Dialog>
  </div>
</template>
