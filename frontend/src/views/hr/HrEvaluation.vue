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
import { useI18n } from '@/i18n'
import { listHrEvaluations, createHrEvaluation, updateHrEvaluation, deleteHrEvaluation, listHrEmployees } from '@/api'

const { t } = useI18n()

const evaluations = ref<any[]>([])
const employees = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editing = ref<any>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const empFilter = ref<number | null>(null)
const gradeOptions = ['A', 'B', 'C', 'D'].map(v => ({ label: v, value: v }))
const form = ref({
  employee_id: null as number | null,
  period: '',
  score: null as number | null,
  grade: '',
  evaluator: '',
  notes: '',
})

async function load() {
  loading.value = true
  try {
    const [e, emp] = await Promise.all([
      listHrEvaluations(companyId.value, empFilter.value || undefined),
      listHrEmployees(companyId.value),
    ])
    evaluations.value = e.data
    employees.value = emp.data
  } finally {
    loading.value = false
  }
}
function openAdd() {
  editing.value = null
  form.value = { employee_id: null, period: '', score: null, grade: '', evaluator: '', notes: '' }
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
    editing.value ? await updateHrEvaluation(editing.value.id, payload) : await createHrEvaluation(payload)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.saveFailed'))
  }
}
async function handleDelete(id: number) {
  if (!confirm('确定删除？')) return
  await deleteHrEvaluation(id)
  await load()
}
onMounted(load)
</script>

<template>
  <div>
    <div class="page-header"><h2>员工考核</h2></div>
    <div class="flex justify-between items-center mb-4">
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
      <Button label="新增考核" icon="pi pi-plus" @click="openAdd" />
    </div>
    <DataTable :value="evaluations" :loading="loading" stripedRows class="text-xs">
      <Column header="员工"
        ><template #body="{ data }">{{
          employees.find((e: any) => e.id === data.employee_id)?.name || '—'
        }}</template></Column
      >
      <Column field="period" header="周期" style="width: 100px" />
      <Column field="score" header="得分" style="width: 80px" />
      <Column header="等级" style="width: 60px"
        ><template #body="{ data }"
          ><Tag
            :value="data.grade"
            :severity="
              data.grade === 'A' ? 'success' : data.grade === 'B' ? 'info' : data.grade === 'C' ? 'warn' : 'danger'
            " /></template
      ></Column>
      <Column field="evaluator" header="评委" style="width: 100px" />
      <Column :header="t('common.remark')" field="notes" />
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
    <Dialog v-model:visible="showDialog" :header="editing ? '编辑考核' : '新增考核'" :style="{ width: '450px' }">
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
        <div>
          <label class="block text-xs text-zinc-500 mb-1">考核周期</label
          ><InputText v-model="form.period" class="w-full" placeholder="如 2026-Q1" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-zinc-500 mb-1">得分</label
            ><InputNumber v-model="form.score" class="w-full" :min-fraction-digits="1" />
          </div>
          <div>
            <label class="block text-xs text-zinc-500 mb-1">等级</label
            ><Dropdown
              v-model="form.grade"
              :options="gradeOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">评委</label
          ><InputText v-model="form.evaluator" class="w-full" />
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
