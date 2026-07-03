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
import { listVehicles, createVehicle, updateVehicle, deleteVehicle } from '@/api'

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = ref(1)
const statusFilter = ref('')
const statuses = ['', '使用中', '闲置', '维修中', '已报废']

const emptyForm = () => ({
  company_id: companyId.value,
  license_plate: '',
  engine_number: '',
  vin: '',
  brand: '',
  model: '',
  insurance_provider: '',
  insurance_policy_no: '',
  insurance_expiry: '',
  insurance_doc_path: '',
  purchase_date: '',
  purchase_price: 0,
  status: '使用中',
  department: '',
  notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const { data } = await listVehicles(companyId.value, statusFilter.value || undefined)
    items.value = data
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
    if (isEdit.value && editId.value) await updateVehicle(editId.value, form.value)
    else await createVehicle(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}
async function remove(id: number) {
  if (!confirm('确定删除？')) return
  try {
    await deleteVehicle(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function insuranceExpiring(expiry: string) {
  if (!expiry) return false
  const d = new Date(expiry)
  const now = new Date()
  const diff = (d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  return diff <= 30 && diff >= 0
}
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <Dropdown v-model="statusFilter" :options="statuses" placeholder="全部状态" @change="load" class="w-28" />
      <Button label="登记车辆" icon="pi pi-plus" @click="openCreate" />
    </div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="license_plate" header="车牌号" sortable />
        <Column field="brand" header="品牌" sortable />
        <Column field="model" header="型号" sortable />
        <Column field="department" header="部门" sortable />
        <Column field="insurance_expiry" header="保险到期" sortable style="min-width: 100px">
          <template #body="{ data }"
            ><span :class="insuranceExpiring(data.insurance_expiry) ? 'text-orange-600 font-semibold' : ''">{{
              data.insurance_expiry || '-'
            }}</span></template
          >
        </Column>
        <Column header="状态" style="min-width: 80px">
          <template #body="{ data }"
            ><Tag
              :value="data.status"
              :severity="
                data.status === '使用中'
                  ? 'success'
                  : data.status === '维修中'
                    ? 'warn'
                    : data.status === '已报废'
                      ? 'danger'
                      : 'info'
              "
          /></template>
        </Column>
        <Column header="操作" style="min-width: 120px">
          <template #body="{ data }">
            <Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" />
            <Button text size="small" icon="pi pi-trash" severity="danger" @click="remove(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑车辆' : '登记车辆'"
      :style="{ width: '600px' }"
      :modal="true"
    >
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">车牌号</label
          ><InputText v-model="form.license_plate" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">品牌</label><InputText v-model="form.brand" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">型号</label><InputText v-model="form.model" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">发动机号</label
          ><InputText v-model="form.engine_number" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">车架号(VIN)</label
          ><InputText v-model="form.vin" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">部门</label
          ><InputText v-model="form.department" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">保险公司</label
          ><InputText v-model="form.insurance_provider" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">保单号</label
          ><InputText v-model="form.insurance_policy_no" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">保险到期日</label
          ><InputText v-model="form.insurance_expiry" type="date" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">保单文件路径</label
          ><InputText v-model="form.insurance_doc_path" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">购买日期</label
          ><InputText v-model="form.purchase_date" type="date" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">购买价格</label
          ><InputNumber v-model="form.purchase_price" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">状态</label
          ><Dropdown v-model="form.status" :options="['使用中', '闲置', '维修中', '已报废']" class="w-full" />
        </div>
        <div class="col-span-3">
          <label class="block text-xs text-zinc-500 mb-1">备注</label
          ><Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="save"
      /></template>
    </Dialog>
  </div>
</template>
