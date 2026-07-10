<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">{{ t('accounting.gl_page.auxLedger') }}</h2>

    <div class="flex gap-3 items-end mb-4 flex-wrap">
      <div>
        <label class="block text-sm mb-1">辅助维度</label>
        <SelectButton
          v-model="filters.aux_type"
          :options="auxTypeOptions"
          optionLabel="label"
          optionValue="value"
          @change="loadAuxObjects"
        />
      </div>
      <div>
        <label class="block text-sm mb-1">{{ auxLabel }}</label>
        <Dropdown
          v-model="filters.aux_id"
          :options="auxObjects"
          optionLabel="name"
          optionValue="id"
          :filter="true"
          placeholder="选择对象"
          class="w-48"
        />
      </div>
      <div>
        <label class="block text-sm mb-1">{{ t('accounting.gl_page.accountCode') }}({{ t('common.optional') }})</label>
        <InputText v-model="filters.account_code" placeholder="如 660" />
      </div>
      <div>
        <label class="block text-sm mb-1">{{ t('accounting.gl_page.startPeriod') }}</label>
        <InputText v-model="filters.start_period" placeholder="yyyy-MM" />
      </div>
      <div>
        <label class="block text-sm mb-1">{{ t('accounting.gl_page.endPeriod') }}</label>
        <InputText v-model="filters.end_period" placeholder="yyyy-MM" />
      </div>
      <Button :label="t('common.search')" icon="pi pi-search" @click="search" />
    </div>

    <div v-if="result">
      <div class="bg-gray-50 p-3 rounded mb-3">
        <strong>{{ result.aux_name }}</strong> | 期初: {{ result.beginning_balance?.toLocaleString() }} | 借方:
        {{ result.total_debit?.toLocaleString() }} | 贷方: {{ result.total_credit?.toLocaleString() }} | 期末:
        {{ result.ending_balance?.toLocaleString() }}
      </div>
      <DataTable :value="result.entries" stripedRows>
        <Column field="date" :header="t('common.date')" style="width: 7rem" />
        <Column field="voucher_no" header="凭证号" style="width: 7rem" />
        <Column field="account_code" header="科目" style="width: 6rem" />
        <Column field="account_name" header="科目名称" style="width: 8rem" />
        <Column field="summary" header="摘要" />
        <Column field="debit" header="借方" style="width: 8rem">
          <template #body="{ data }">{{ data.debit ? data.debit.toLocaleString() : '' }}</template>
        </Column>
        <Column field="credit" header="贷方" style="width: 8rem">
          <template #body="{ data }">{{ data.credit ? data.credit.toLocaleString() : '' }}</template>
        </Column>
        <Column field="balance" :header="t('accounting.gl_page.balance')" style="width: 8rem">
          <template #body="{ data }">{{ data.balance?.toLocaleString() }}</template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from '@/i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import SelectButton from 'primevue/selectbutton'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { getAuxLedger } from '../../api'
import { listDepartments, listPersons, listCounterparties, listProjects } from '../../api'

const toast = useToast()
const { t } = useI18n()
const companyId = Number(localStorage.getItem('companyId') || '1')
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const auxTypeOptions = [
  { label: '部门', value: 'department' },
  { label: '个人', value: 'person' },
  { label: '往来单位', value: 'counterparty' },
  { label: '项目', value: 'project' },
]

const filters = ref({
  aux_type: 'department' as string,
  aux_id: null as number | null,
  account_code: '',
  start_period: defaultPeriod,
  end_period: defaultPeriod,
})

const auxObjects = ref<any[]>([])
const result = ref<any>(null)

const auxLabel = computed(() => {
  const m: Record<string, string> = { department: '部门', person: '个人', counterparty: '往来单位', project: '项目' }
  return m[filters.value.aux_type] || ''
})

async function loadAuxObjects() {
  try {
    const type = filters.value.aux_type
    let data: any[] = []
    if (type === 'department') {
      const res = await listDepartments(companyId)
      data = res.data
    } else if (type === 'person') {
      const res = await listPersons(companyId)
      data = res.data
    } else if (type === 'counterparty') {
      const res = await listCounterparties(companyId)
      data = res.data
    } else if (type === 'project') {
      const res = await listProjects(companyId)
      data = res.data
    }
    auxObjects.value = data
  } catch (_e) {
    auxObjects.value = []
  }
}

loadAuxObjects()

async function search() {
  if (!filters.value.aux_id) {
    toast.add({ severity: 'warn', summary: '请选择辅助核算对象', life: 3000 })
    return
  }
  try {
    const { data } = await getAuxLedger(
      companyId,
      filters.value.aux_type,
      filters.value.aux_id,
      filters.value.start_period,
      filters.value.end_period,
      filters.value.account_code || undefined,
    )
    result.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}
</script>
