<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import {
  listVehicleMaintenance,
  createVehicleMaintenance,
  updateVehicleMaintenance,
  deleteVehicleMaintenance,
  submitVehicleMaintenance,
  listVehicles,
} from '@/api'

const items = ref<any[]>([])
const vehicles = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = ref(1)
const emptyForm = () => ({
  company_id: companyId.value,
  vehicle_id: 0,
  maintenance_type: '日常保养',
  vendor: '',
  estimated_cost: 0,
  actual_cost: null,
  description: '',
})
const form = ref(emptyForm())
const maintTypes = ['日常保养', '维修', '事故维修']

async function load() {
  loading.value = true
  try {
    const [r1, r2] = await Promise.all([listVehicleMaintenance(companyId.value), listVehicles(companyId.value)])
    items.value = r1.data
    vehicles.value = r2.data
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
    if (isEdit.value && editId.value) await updateVehicleMaintenance(editId.value, form.value)
    else await createVehicleMaintenance(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}
async function remove(id: number) {
  if (!confirm('确定删除？')) return
  try {
    await deleteVehicleMaintenance(id)
    await load()
  } catch (_e: any) {
    alert('删除失败')
  }
}
async function doSubmit(id: number) {
  const ids = prompt('请输入审批人ID（逗号分隔）：')
  if (!ids) return
  try {
    await submitVehicleMaintenance(id, ids.split(',').map(Number))
    await load()
  } catch (_e: any) {
    alert('提交失败')
  }
}
const vehiclePlate = (id: number) => vehicles.value.find((v: any) => v.id === id)?.license_plate || `车辆#${id}`
const statusSeverity = (s: string) =>
  (
    ({
      draft: 'secondary',
      pending_approval: 'warn',
      approved: 'success',
      rejected: 'danger',
      completed: 'info',
    }) as any
  )[s] || 'secondary'
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-end mb-4"><Button label="新建维保申请" icon="pi pi-plus" @click="openCreate" /></div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column header="车辆" sortable
          ><template #body="{ data }">{{ vehiclePlate(data.vehicle_id) }}</template></Column
        >
        <Column field="maintenance_type" header="维保类型" sortable />
        <Column field="vendor" header="维修商" sortable />
        <Column field="estimated_cost" header="预估费用" sortable />
        <Column header="状态"
          ><template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template
        ></Column>
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
      :header="isEdit ? '编辑维保申请' : '新建维保申请'"
      :style="{ width: '500px' }"
      :modal="true"
    >
      <div class="grid grid-cols-2 gap-3">
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">车辆</label
          ><Dropdown
            v-model="form.vehicle_id"
            :options="vehicles"
            optionLabel="license_plate"
            optionValue="id"
            placeholder="选择车辆"
            class="w-full"
            filter
          />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">维保类型</label
          ><Dropdown v-model="form.maintenance_type" :options="maintTypes" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">维修商</label
          ><InputText v-model="form.vendor" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">预估费用</label
          ><InputNumber v-model="form.estimated_cost" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">实际费用</label
          ><InputNumber v-model="form.actual_cost" class="w-full" />
        </div>
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">描述</label
          ><Textarea v-model="form.description" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="save"
      /></template>
    </Dialog>
  </div>
</template>
