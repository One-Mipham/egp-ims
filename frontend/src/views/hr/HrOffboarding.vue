<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import {
  listHrOffboarding,
  createHrOffboarding,
  updateHrOffboarding,
  deleteHrOffboarding,
  listHrEmployees,
} from '@/api'

const records = ref<any[]>([])
const employees = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editing = ref<any>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const statusOptions = ['申请', '审批中', '已批准', '已离职'].map(v => ({ label: v, value: v }))
const activeEmployees = computed(() => employees.value.filter((e: any) => e.status === '在职'))
const form = ref({
  employee_id: null as number | null,
  apply_date: '',
  last_day: '',
  reason: '',
  handover_to: '',
  status: '申请',
  notes: '',
})

async function load() {
  loading.value = true
  try {
    const [o, e] = await Promise.all([listHrOffboarding(companyId.value), listHrEmployees(companyId.value)])
    records.value = o.data
    employees.value = e.data
  } finally {
    loading.value = false
  }
}
function openAdd() {
  editing.value = null
  form.value = {
    employee_id: null,
    apply_date: '',
    last_day: '',
    reason: '',
    handover_to: '',
    status: '申请',
    notes: '',
  }
  showDialog.value = true
}
function openEdit(row: any) {
  editing.value = row
  form.value = { ...row }
  showDialog.value = true
}
async function save() {
  try {
    const payload = { ...form.value, company_id: companyId.value }
    editing.value ? await updateHrOffboarding(editing.value.id, payload) : await createHrOffboarding(payload)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  }
}
async function handleDelete(id: number) {
  if (!confirm('确定删除？')) return
  await deleteHrOffboarding(id)
  await load()
}
onMounted(load)
</script>

<template>
  <div>
    <div class="page-header"><h2>员工离职</h2></div>
    <div class="flex justify-end mb-4"><Button label="新增离职" icon="pi pi-plus" @click="openAdd" /></div>
    <DataTable :value="records" :loading="loading" stripedRows class="text-xs">
      <Column header="员工"
        ><template #body="{ data }">{{
          employees.find((e: any) => e.id === data.employee_id)?.name || '—'
        }}</template></Column
      >
      <Column field="apply_date" header="申请日期" style="width: 100px" />
      <Column field="last_day" header="最后工作日" style="width: 100px" />
      <Column field="reason" header="离职原因" style="width: 150px" />
      <Column field="handover_to" header="交接人" style="width: 80px" />
      <Column header="状态" style="width: 80px"
        ><template #body="{ data }"
          ><Tag
            :value="data.status"
            :severity="data.status === '已离职' ? 'danger' : data.status === '已批准' ? 'success' : 'info'" /></template
      ></Column>
      <Column header="操作" style="width: 120px"
        ><template #body="{ data }"
          ><Button label="编辑" text size="small" @click="openEdit(data)" /><Button
            label="删除"
            text
            severity="danger"
            size="small"
            @click="handleDelete(data.id)" /></template
      ></Column>
    </DataTable>
    <Dialog v-model:visible="showDialog" :header="editing ? '编辑离职' : '新增离职'" :style="{ width: '480px' }">
      <div class="flex flex-col gap-3 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">员工</label
          ><Dropdown
            v-model="form.employee_id"
            :options="editing ? employees : activeEmployees"
            option-label="name"
            option-value="id"
            class="w-full"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-zinc-500 mb-1">申请日期</label
            ><InputText v-model="form.apply_date" type="date" class="w-full" />
          </div>
          <div>
            <label class="block text-xs text-zinc-500 mb-1">最后工作日</label
            ><InputText v-model="form.last_day" type="date" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">离职原因</label
          ><Textarea v-model="form.reason" rows="2" class="w-full" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-zinc-500 mb-1">交接人</label
            ><InputText v-model="form.handover_to" class="w-full" />
          </div>
          <div>
            <label class="block text-xs text-zinc-500 mb-1">状态</label
            ><Dropdown
              v-model="form.status"
              :options="statusOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">备注</label
          ><Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
        <Button label="保存" icon="pi pi-check" @click="save" />
      </div>
    </Dialog>
  </div>
</template>
