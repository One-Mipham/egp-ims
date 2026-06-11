<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'; import Column from 'primevue/column'
import Button from 'primevue/button'; import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'; import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'; import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import { listHrTrainings, createHrTraining, updateHrTraining, deleteHrTraining, listHrEmployees } from '@/api'

const trainings = ref<any[]>([]); const employees = ref<any[]>([])
const loading = ref(false); const showDialog = ref(false); const editing = ref<any>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const empFilter = ref<number | null>(null)
const statusOptions = ['计划中', '进行中', '已完成', '已取消'].map(v => ({ label: v, value: v }))
const form = ref({ employee_id: null as number | null, training_name: '', training_date: '', provider: '', cost: null as number | null, status: '计划中', notes: '' })

async function load() {
  loading.value = true
  try {
    const [t, e] = await Promise.all([
      listHrTrainings(companyId.value, empFilter.value || undefined),
      listHrEmployees(companyId.value, '在职'),
    ])
    trainings.value = t.data; employees.value = e.data
  } finally { loading.value = false }
}
function openAdd() { editing.value = null; form.value = { employee_id: null, training_name: '', training_date: '', provider: '', cost: null, status: '计划中', notes: '' }; showDialog.value = true }
function openEdit(row: any) { editing.value = row; form.value = { ...row }; showDialog.value = true }
async function save() {
  try {
    const payload = { ...form.value, company_id: companyId.value }
    editing.value ? await updateHrTraining(editing.value.id, payload) : await createHrTraining(payload)
    showDialog.value = false; await load()
  } catch (e: any) { alert(e.response?.data?.detail || '保存失败') }
}
async function handleDelete(id: number) { if (!confirm('确定删除？')) return; await deleteHrTraining(id); await load() }
onMounted(load)
</script>

<template>
  <div>
    <div class="page-header"><h2>员工培训</h2></div>
    <div class="flex justify-between items-center mb-4">
      <Dropdown v-model="empFilter" :options="employees" option-label="name" option-value="id" placeholder="筛选员工" class="w-40 text-xs" @change="load" showClear />
      <Button label="新增培训" icon="pi pi-plus" @click="openAdd" />
    </div>
    <DataTable :value="trainings" :loading="loading" stripedRows class="text-xs">
      <Column header="员工"><template #body="{ data }">{{ employees.find((e: any) => e.id === data.employee_id)?.name || '—' }}</template></Column>
      <Column field="training_name" header="培训名称" />
      <Column field="training_date" header="日期" style="width:100px" />
      <Column field="provider" header="机构" style="width:120px" />
      <Column field="cost" header="费用" style="width:80px" />
      <Column header="状态" style="width:80px"><template #body="{ data }"><Tag :value="data.status" :severity="data.status === '已完成' ? 'success' : 'info'" /></template></Column>
      <Column header="操作" style="width:120px"><template #body="{ data }"><Button label="编辑" text size="small" @click="openEdit(data)" /><Button label="删除" text severity="danger" size="small" @click="handleDelete(data.id)" /></template></Column>
    </DataTable>
    <Dialog v-model:visible="showDialog" :header="editing ? '编辑培训' : '新增培训'" :style="{ width: '480px' }">
      <div class="flex flex-col gap-3 py-4">
        <div><label class="block text-xs text-zinc-500 mb-1">员工</label><Dropdown v-model="form.employee_id" :options="employees" option-label="name" option-value="id" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">培训名称 *</label><InputText v-model="form.training_name" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">日期</label><InputText v-model="form.training_date" type="date" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">培训机构</label><InputText v-model="form.provider" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">费用</label><InputNumber v-model="form.cost" class="w-full" mode="currency" currency="CNY" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">状态</label><Dropdown v-model="form.status" :options="statusOptions" option-label="label" option-value="value" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">备注</label><Textarea v-model="form.notes" rows="2" class="w-full" /></div>
        <Button label="保存" icon="pi pi-check" @click="save" />
      </div>
    </Dialog>
  </div>
</template>
