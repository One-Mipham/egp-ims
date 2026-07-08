<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useI18n } from '@/i18n'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import {
  listExpensePolicies,
  createExpensePolicy,
  updateExpensePolicy,
  deleteExpensePolicy,
  listExpenseItems,
} from '@/api/expenses'

const { t } = useI18n()
const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const policies = ref<any[]>([])
const expenseItems = ref<any[]>([])
const dialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const loading = ref(false)

const form = ref({
  expense_item_id: null as number | null,
  country: '',
  region: '',
  department_id: null as number | null,
  position_level: null as number | null,
  policy_type: 'event',
  max_amount: 0,
  currency: 'CNY',
  effective_from: '',
  effective_to: '',
  notes: '',
})

const policyTypeOptions = [
  { label: '单次标准 (event)', value: 'event' },
  { label: '日标准 (daily)', value: 'daily' },
  { label: '人均标准 (per_person)', value: 'per_person' },
]

const fetchAll = async () => {
  loading.value = true
  try {
    const [pRes, iRes] = await Promise.all([listExpensePolicies(companyId), listExpenseItems(companyId)])
    policies.value = pRes.data
    expenseItems.value = iRes.data
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e.message, life: 3000 })
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEdit.value = false
  editId.value = null
  form.value = {
    expense_item_id: null,
    country: '',
    region: '',
    department_id: null,
    position_level: null,
    policy_type: 'event',
    max_amount: 0,
    currency: 'CNY',
    effective_from: '',
    effective_to: '',
    notes: '',
  }
  dialog.value = true
}

const openEdit = (p: any) => {
  isEdit.value = true
  editId.value = p.id
  form.value = {
    expense_item_id: p.expense_item_id,
    country: p.country || '',
    region: p.region || '',
    department_id: p.department_id,
    position_level: p.position_level,
    policy_type: p.policy_type,
    max_amount: p.max_amount,
    currency: p.currency || 'CNY',
    effective_from: p.effective_from,
    effective_to: p.effective_to || '',
    notes: p.notes || '',
  }
  dialog.value = true
}

const save = async () => {
  try {
    const data = {
      company_id: companyId,
      expense_item_id: form.value.expense_item_id ?? undefined,
      country: form.value.country || undefined,
      region: form.value.region || undefined,
      department_id: form.value.department_id ?? undefined,
      position_level: form.value.position_level ?? undefined,
      policy_type: form.value.policy_type,
      max_amount: form.value.max_amount,
      currency: form.value.currency,
      effective_from: form.value.effective_from,
      effective_to: form.value.effective_to || undefined,
      notes: form.value.notes || undefined,
    }
    if (isEdit.value && editId.value) {
      await updateExpensePolicy(editId.value, data)
      toast.add({ severity: 'success', summary: '已更新', life: 2000 })
    } else {
      await createExpensePolicy(data)
      toast.add({ severity: 'success', summary: '已创建', life: 2000 })
    }
    dialog.value = false
    fetchAll()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.saveFailed'), detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

const remove = async (id: number) => {
  try {
    await deleteExpensePolicy(id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    fetchAll()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.deleteFailed'), detail: e.message, life: 3000 })
  }
}

const getItemName = (id: number) => expenseItems.value.find((i: any) => i.id === id)?.name || '-'

onMounted(fetchAll)
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold">7.5 费用标准</h1>
      <Button label="新增费用标准" icon="pi pi-plus" @click="openCreate" />
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="policies" :loading="loading" stripedRows size="small" class="text-sm">
        <Column header="费用类型">
          <template #body="slotProps">{{ getItemName(slotProps.data.expense_item_id) }}</template>
        </Column>
        <Column field="country" header="国别" />
        <Column field="region" header="地区" />
        <Column field="policy_type" header="标准类型">
          <template #body="slotProps">
            <Tag
              :value="
                slotProps.data.policy_type === 'daily'
                  ? '日标准'
                  : slotProps.data.policy_type === 'per_person'
                    ? '人均'
                    : '单次'
              "
            />
          </template>
        </Column>
        <Column field="max_amount" header="上限金额">
          <template #body="slotProps">
            {{ slotProps.data.currency }} {{ slotProps.data.max_amount.toLocaleString() }}
          </template>
        </Column>
        <Column field="effective_from" header="生效日期" />
        <Column field="effective_to" header="失效日期">
          <template #body="slotProps">{{ slotProps.data.effective_to || '长期' }}</template>
        </Column>
        <Column :header="t('common.actions')" style="width: 8rem">
          <template #body="slotProps">
            <Button icon="pi pi-pencil" size="small" text rounded @click="openEdit(slotProps.data)" />
            <Button icon="pi pi-trash" size="small" text rounded severity="danger" @click="remove(slotProps.data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog
      v-model:visible="dialog"
      :header="isEdit ? '编辑费用标准' : '新增费用标准'"
      :modal="true"
      :style="{ width: '32rem' }"
    >
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">费用类型</label>
            <Dropdown
              v-model="form.expense_item_id"
              :options="expenseItems"
              optionLabel="name"
              optionValue="id"
              class="w-full"
              showClear
              placeholder="选择费用类型"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">标准类型</label>
            <Dropdown
              v-model="form.policy_type"
              :options="policyTypeOptions"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">国别</label>
            <InputText v-model="form.country" class="w-full" placeholder="如 CN" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">地区</label>
            <InputText v-model="form.region" class="w-full" placeholder="如 北京" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">上限金额</label>
            <InputNumber v-model="form.max_amount" class="w-full" :minFractionDigits="2" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">币种</label>
            <InputText v-model="form.currency" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">生效日期</label>
            <InputText type="date" v-model="form.effective_from" class="w-full" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">失效日期</label>
            <InputText type="date" v-model="form.effective_to" class="w-full" />
          </div>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ t('common.remark') }}</label>
          <Textarea v-model="form.notes" class="w-full" rows="2" placeholder="如参照《差旅管理办法》2024版" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="dialog = false" />
        <Button :label="t('common.save')" @click="save" />
      </template>
    </Dialog>
  </div>
</template>
