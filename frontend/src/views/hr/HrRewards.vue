<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import { listHrRewards, createHrReward, updateHrReward, deleteHrReward, listHrEmployees } from '@/api'

const rewards = ref<any[]>([])
const employees = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editing = ref<any>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const form = ref({
  employee_id: null as number | null,
  type: '奖励',
  date: '',
  description: '',
  amount: null as number | null,
  approved_by: '',
})

async function load() {
  loading.value = true
  try {
    const [r, e] = await Promise.all([listHrRewards(companyId.value), listHrEmployees(companyId.value)])
    rewards.value = r.data
    employees.value = e.data
  } finally {
    loading.value = false
  }
}
function openAdd() {
  editing.value = null
  form.value = { employee_id: null, type: '奖励', date: '', description: '', amount: null, approved_by: '' }
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
    editing.value ? await updateHrReward(editing.value.id, payload) : await createHrReward(payload)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  }
}
async function handleDelete(id: number) {
  if (!confirm('确定删除？')) return
  await deleteHrReward(id)
  await load()
}
onMounted(load)
</script>

<template>
  <div>
    <div class="page-header"><h2>员工奖惩</h2></div>
    <div class="flex justify-end mb-4"><Button label="新增记录" icon="pi pi-plus" @click="openAdd" /></div>
    <DataTable :value="rewards" :loading="loading" stripedRows class="text-xs">
      <Column header="员工"
        ><template #body="{ data }">{{
          employees.find((e: any) => e.id === data.employee_id)?.name || '—'
        }}</template></Column
      >
      <Column header="类型" style="width: 70px"
        ><template #body="{ data }"
          ><Tag :value="data.type" :severity="data.type === '奖励' ? 'success' : 'danger'" /></template
      ></Column>
      <Column field="date" header="日期" style="width: 100px" />
      <Column field="description" header="描述" />
      <Column field="amount" header="金额" style="width: 100px"
        ><template #body="{ data }">{{ data.amount?.toLocaleString() }}</template></Column
      >
      <Column field="approved_by" header="批准人" style="width: 80px" />
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
    <Dialog v-model:visible="showDialog" :header="editing ? '编辑记录' : '新增记录'" :style="{ width: '450px' }">
      <div class="flex flex-col gap-3 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">员工</label
          ><Dropdown
            v-model="form.employee_id"
            :options="employees"
            option-label="name"
            option-value="id"
            class="w-full"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-zinc-500 mb-1">类型</label
            ><Dropdown
              v-model="form.type"
              :options="[
                { label: '奖励', value: '奖励' },
                { label: '惩罚', value: '惩罚' },
              ]"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
          <div>
            <label class="block text-xs text-zinc-500 mb-1">日期</label
            ><InputText v-model="form.date" type="date" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-zinc-500 mb-1">金额</label
            ><InputNumber v-model="form.amount" class="w-full" mode="currency" currency="CNY" />
          </div>
          <div>
            <label class="block text-xs text-zinc-500 mb-1">批准人</label
            ><InputText v-model="form.approved_by" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">描述</label
          ><Textarea v-model="form.description" rows="2" class="w-full" />
        </div>
        <Button label="保存" icon="pi pi-check" @click="save" />
      </div>
    </Dialog>
  </div>
</template>
