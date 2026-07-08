<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import { useI18n } from '@/i18n'
import { listHrSalaries, createHrSalary, updateHrSalary, deleteHrSalary, listHrEmployees } from '@/api'

const { t } = useI18n()

const salaries = ref<any[]>([])
const employees = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editing = ref<any>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const empFilter = ref<number | null>(null)
const monthFilter = ref('')
const form = ref({
  employee_id: null as number | null,
  year_month: '',
  base_salary: 0,
  bonus: 0,
  allowance: 0,
  deduction: 0,
  net_salary: 0,
  notes: '',
})

async function load() {
  loading.value = true
  try {
    const [s, e] = await Promise.all([
      listHrSalaries(companyId.value, empFilter.value || undefined, monthFilter.value || undefined),
      listHrEmployees(companyId.value),
    ])
    salaries.value = s.data
    employees.value = e.data
  } finally {
    loading.value = false
  }
}
function calcNet() {
  form.value.net_salary =
    (form.value.base_salary || 0) + (form.value.bonus || 0) + (form.value.allowance || 0) - (form.value.deduction || 0)
}
function openAdd() {
  editing.value = null
  form.value = {
    employee_id: null,
    year_month: '',
    base_salary: 0,
    bonus: 0,
    allowance: 0,
    deduction: 0,
    net_salary: 0,
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
  calcNet()
  try {
    const payload = { ...form.value, company_id: companyId.value }
    editing.value ? await updateHrSalary(editing.value.id, payload) : await createHrSalary(payload)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.saveFailed'))
  }
}
async function handleDelete(id: number) {
  if (!confirm('确定删除？')) return
  await deleteHrSalary(id)
  await load()
}
onMounted(load)
</script>

<template>
  <div>
    <div class="page-header"><h2>{{ t('hr.salaries') }}</h2></div>
    <div class="flex justify-between items-center mb-4 gap-2 flex-wrap">
      <div class="flex gap-2">
        <Dropdown
          v-model="empFilter"
          :options="employees"
          option-label="name"
          option-value="id"
          placeholder="筛选员工"
          class="w-40 text-xs"
          @change="load"
          showClear
        />
        <InputText v-model="monthFilter" placeholder="月份 如2026-05" class="w-36 text-xs" @change="load" />
      </div>
      <Button label="新增薪酬" icon="pi pi-plus" @click="openAdd" />
    </div>
    <DataTable :value="salaries" :loading="loading" stripedRows class="text-xs">
      <Column header="员工"
        ><template #body="{ data }">{{
          employees.find((e: any) => e.id === data.employee_id)?.name || '—'
        }}</template></Column
      >
      <Column field="year_month" header="月份" style="width: 90px" />
      <Column field="base_salary" header="基本工资" style="width: 100px"
        ><template #body="{ data }">{{ data.base_salary?.toLocaleString() }}</template></Column
      >
      <Column field="bonus" header="奖金" style="width: 80px"
        ><template #body="{ data }">{{ data.bonus?.toLocaleString() }}</template></Column
      >
      <Column field="allowance" header="津贴" style="width: 80px"
        ><template #body="{ data }">{{ data.allowance?.toLocaleString() }}</template></Column
      >
      <Column field="deduction" header="扣款" style="width: 80px"
        ><template #body="{ data }">{{ data.deduction?.toLocaleString() }}</template></Column
      >
      <Column field="net_salary" header="实发" style="width: 100px"
        ><template #body="{ data }"
          ><span class="font-semibold">{{ data.net_salary?.toLocaleString() }}</span></template
        ></Column
      >
      <Column :header="t('common.actions')" style="width: 120px"
        ><template #body="{ data }"
          ><Button label="编辑" text size="small" @click="openEdit(data)" /><Button
            :label="t('common.delete')"
            text
            severity="danger"
            size="small"
            @click="handleDelete(data.id)" /></template
      ></Column>
    </DataTable>
    <Dialog v-model:visible="showDialog" :header="editing ? '编辑薪酬' : '新增薪酬'" :style="{ width: '500px' }">
      <div class="flex flex-col gap-3 py-4">
        <div class="grid grid-cols-2 gap-3">
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
          <div>
            <label class="block text-xs text-zinc-500 mb-1">月份 *</label
            ><InputText v-model="form.year_month" class="w-full" placeholder="2026-05" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-zinc-500 mb-1">基本工资</label
            ><InputNumber v-model="form.base_salary" class="w-full" mode="currency" currency="CNY" @input="calcNet" />
          </div>
          <div>
            <label class="block text-xs text-zinc-500 mb-1">奖金</label
            ><InputNumber v-model="form.bonus" class="w-full" mode="currency" currency="CNY" @input="calcNet" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-zinc-500 mb-1">津贴</label
            ><InputNumber v-model="form.allowance" class="w-full" mode="currency" currency="CNY" @input="calcNet" />
          </div>
          <div>
            <label class="block text-xs text-zinc-500 mb-1">扣款</label
            ><InputNumber v-model="form.deduction" class="w-full" mode="currency" currency="CNY" @input="calcNet" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">实发（自动计算）</label
          ><InputNumber v-model="form.net_salary" class="w-full" disabled mode="currency" currency="CNY" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">{{ t('common.remark') }}</label
          ><Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
        <Button :label="t('common.save')" icon="pi pi-check" @click="save" />
      </div>
    </Dialog>
  </div>
</template>
