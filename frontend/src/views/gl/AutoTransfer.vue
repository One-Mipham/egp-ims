<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold">自动转账模板</h2>
      <Button label="新建模板" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable :value="templates" stripedRows class="mb-4">
      <Column field="name" header="模板名称" />
      <Column field="template_type" header="类型">
        <template #body="{ data }">
          <Tag
            :value="typeLabel(data.template_type)"
            :severity="data.template_type === 'fixed' ? 'info' : data.template_type === 'ratio' ? 'warn' : 'success'"
          />
        </template>
      </Column>
      <Column field="frequency" header="频率">
        <template #body="{ data }">{{ freqLabel(data.frequency) }}</template>
      </Column>
      <Column field="entries" header="分录数">
        <template #body="{ data }">{{ data.entries?.length || 0 }}</template>
      </Column>
      <Column field="is_active" header="启用">
        <template #body="{ data }">
          <i :class="data.is_active ? 'pi pi-check text-green-500' : 'pi pi-times text-gray-400'" />
        </template>
      </Column>
      <Column header="操作" style="width: 16rem">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button
              icon="pi pi-play"
              severity="success"
              size="small"
              label="执行"
              @click="execute(data)"
              :disabled="!data.is_active"
            />
            <Button icon="pi pi-pencil" severity="info" size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" severity="danger" size="small" @click="confirmDelete(data)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialogVisible"
      :header="isEditing ? '编辑模板' : '新建模板'"
      :modal="true"
      :style="{ width: '700px' }"
    >
      <div class="flex flex-col gap-3">
        <div class="flex gap-3">
          <div class="flex-1">
            <label class="block text-sm mb-1">模板名称</label>
            <InputText v-model="form.name" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">频率</label>
            <Dropdown v-model="form.frequency" :options="frequencyOptions" optionLabel="label" optionValue="value" />
          </div>
        </div>
        <div>
          <label class="block text-sm mb-1">类型</label>
          <SelectButton v-model="form.template_type" :options="typeOptions" optionLabel="label" optionValue="value" />
        </div>
        <div>
          <label class="block text-sm mb-1">说明</label>
          <Textarea v-model="form.description" rows="2" class="w-full" />
        </div>
        <div>
          <div class="flex justify-between items-center mb-2">
            <label class="text-sm font-medium">分录定义</label>
            <Button icon="pi pi-plus" size="small" severity="secondary" label="添加分录" @click="addEntry" />
          </div>
          <DataTable :value="form.entries" size="small">
            <Column header="科目代码" style="width: 8rem">
              <template #body="{ data, index }">
                <InputText v-model="data.account_code" size="small" class="w-full" />
              </template>
            </Column>
            <Column header="方向" style="width: 5rem">
              <template #body="{ data, index }">
                <Dropdown v-model="data.direction" :options="['debit', 'credit']" size="small">
                  <template #value="slotProps">{{ slotProps.value === 'debit' ? '借' : '贷' }}</template>
                  <template #option="slotProps">{{ slotProps.option === 'debit' ? '借方' : '贷方' }}</template>
                </Dropdown>
              </template>
            </Column>
            <Column header="公式" style="width: 7rem">
              <template #body="{ data, index }">
                <InputText
                  v-model="data.formula"
                  size="small"
                  class="w-full"
                  :placeholder="form.template_type === 'fixed' ? '金额' : '百分比/余额'"
                />
              </template>
            </Column>
            <Column header="摘要">
              <template #body="{ data, index }">
                <InputText v-model="data.summary" size="small" class="w-full" />
              </template>
            </Column>
            <Column header="" style="width: 3rem">
              <template #body="{ index }">
                <Button icon="pi pi-times" severity="danger" size="small" text rounded @click="removeEntry(index)" />
              </template>
            </Column>
          </DataTable>
        </div>
        <div class="flex items-center gap-2">
          <Checkbox v-model="form.is_active" :binary="true" inputId="is_active" />
          <label for="is_active">启用</label>
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="dialogVisible = false" />
        <Button label="保存" @click="save" />
      </template>
    </Dialog>

    <Dialog v-model:visible="execDialogVisible" header="执行自动转账" :modal="true" :style="{ width: '400px' }">
      <div class="flex flex-col gap-3">
        <p>
          执行模板: <strong>{{ execTarget?.name }}</strong>
        </p>
        <div>
          <label class="block text-sm mb-1">执行期间</label>
          <InputText v-model="execPeriod" placeholder="yyyy-MM" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="execDialogVisible = false" />
        <Button label="执行" severity="success" @click="confirmExecute" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import SelectButton from 'primevue/selectbutton'
import Checkbox from 'primevue/checkbox'
import Tag from 'primevue/tag'
import {
  listAutoTransferTemplates,
  createAutoTransferTemplate,
  updateAutoTransferTemplate,
  deleteAutoTransferTemplate,
  executeAutoTransfer,
} from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')

const templates = ref<any[]>([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const execDialogVisible = ref(false)
const execTarget = ref<any>(null)
const execPeriod = ref('')

const frequencyOptions = [
  { label: '手动', value: 'manual' },
  { label: '每月', value: 'monthly' },
  { label: '每季', value: 'quarterly' },
  { label: '每年', value: 'yearly' },
]

const typeOptions = [
  { label: '固定金额', value: 'fixed' },
  { label: '按比例', value: 'ratio' },
  { label: '余额结转', value: 'balance' },
]

const defaultEntry = { account_code: '', direction: 'credit', formula: '', summary: '' }

const form = ref({
  company_id: companyId,
  name: '',
  description: '',
  template_type: 'fixed',
  frequency: 'manual',
  is_active: true,
  entries: [{ ...defaultEntry }] as any[],
})

function typeLabel(t: string) {
  const m: Record<string, string> = { fixed: '固定金额', ratio: '按比例', balance: '余额结转' }
  return m[t] || t
}

function freqLabel(f: string) {
  const m: Record<string, string> = { manual: '手动', monthly: '每月', quarterly: '每季', yearly: '每年' }
  return m[f] || f
}

async function load() {
  const { data } = await listAutoTransferTemplates(companyId)
  templates.value = data
}

function openCreate() {
  isEditing.value = false
  editingId.value = null
  form.value = {
    company_id: companyId,
    name: '',
    description: '',
    template_type: 'fixed',
    frequency: 'manual',
    is_active: true,
    entries: [{ ...defaultEntry }],
  }
  dialogVisible.value = true
}

function openEdit(t: any) {
  isEditing.value = true
  editingId.value = t.id
  form.value = {
    company_id: companyId,
    name: t.name,
    description: t.description || '',
    template_type: t.template_type,
    frequency: t.frequency,
    is_active: t.is_active,
    entries: (t.entries || []).map((e: any) => ({ ...e })),
  }
  dialogVisible.value = true
}

function addEntry() {
  form.value.entries.push({ ...defaultEntry })
}
function removeEntry(index: number) {
  form.value.entries.splice(index, 1)
}

async function save() {
  try {
    if (isEditing.value && editingId.value) {
      await updateAutoTransferTemplate(editingId.value, {
        name: form.value.name,
        description: form.value.description,
        template_type: form.value.template_type,
        frequency: form.value.frequency,
        is_active: form.value.is_active,
        entries: form.value.entries,
      })
      toast.add({ severity: 'success', summary: '已更新', life: 3000 })
    } else {
      await createAutoTransferTemplate({
        company_id: companyId,
        name: form.value.name,
        description: form.value.description,
        template_type: form.value.template_type,
        frequency: form.value.frequency,
        is_active: form.value.is_active,
        entries: form.value.entries,
      })
      toast.add({ severity: 'success', summary: '已创建', life: 3000 })
    }
    dialogVisible.value = false
    await load()
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '保存失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

async function confirmDelete(t: any) {
  if (!confirm(`确定删除模板 "${t.name}" 吗？`)) return
  await deleteAutoTransferTemplate(t.id)
  toast.add({ severity: 'success', summary: '已删除', life: 3000 })
  await load()
}

function execute(t: any) {
  execTarget.value = t
  execPeriod.value = new Date().toISOString().slice(0, 7)
  execDialogVisible.value = true
}

async function confirmExecute() {
  if (!execTarget.value) return
  try {
    const { data } = await executeAutoTransfer(execTarget.value.id, companyId, execPeriod.value)
    toast.add({ severity: 'success', summary: '转账已执行', detail: `凭证号: ${data.voucher_no}`, life: 5000 })
    execDialogVisible.value = false
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '执行失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

onMounted(load)
</script>
