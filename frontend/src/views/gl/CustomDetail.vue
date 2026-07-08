<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">{{ t('accounting.gl_page.customDetail') }}</h2>

    <div class="border rounded p-3 mb-4">
      <div class="flex gap-2 items-end flex-wrap mb-3">
        <div>
          <label class="text-xs block mb-1">起始日期</label>
          <InputText v-model="filters.start_date" size="small" placeholder="yyyy-MM-dd" class="w-32" />
        </div>
        <div>
          <label class="text-xs block mb-1">截止日期</label>
          <InputText v-model="filters.end_date" size="small" placeholder="yyyy-MM-dd" class="w-32" />
        </div>
        <div>
          <label class="text-xs block mb-1">{{ t('accounting.gl_page.accountCode') }}</label>
          <InputText v-model="filters.account_code" size="small" placeholder="如 660" class="w-28" />
        </div>
        <Button :label="t('common.search')" icon="pi pi-search" size="small" @click="search" />
        <Button label="导出CSV" icon="pi pi-download" size="small" severity="secondary" @click="exportCsv" />
      </div>
      <div>
        <label class="text-xs block mb-1">选择列</label>
        <div class="flex flex-wrap gap-1">
          <Chip
            v-for="col in columns"
            :key="col.field"
            :class="{ 'bg-blue-100': selectedCols.includes(col.field) }"
            :label="col.header"
            class="cursor-pointer"
            @click="toggleCol(col.field)"
          />
        </div>
      </div>
    </div>

    <DataTable :value="results" stripedRows size="small" class="mb-4" scrollable scrollHeight="600px">
      <Column
        v-for="col in visibleCols"
        :key="col.field"
        :field="col.field"
        :header="col.header"
        style="min-width: 6rem"
      />
    </DataTable>
    <div class="text-sm text-gray-500">{{ results.length }} 条记录</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from '@/i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { getCustomDetailColumns, queryCustomDetail, exportCustomDetail } from '../../api'

const toast = useToast()
const { t } = useI18n()
const companyId = Number(localStorage.getItem('company_id') || '1')
const now = new Date()

const columns = ref<{ field: string; header: string }[]>([])
const selectedCols = ref<string[]>(['date', 'voucher_no', 'account_code', 'account_name', 'summary', 'debit', 'credit'])

const filters = ref({
  start_date: `${now.getFullYear()}-01-01`,
  end_date: `${now.getFullYear()}-12-31`,
  account_code: '',
})

const results = ref<any[]>([])

const visibleCols = computed(() => columns.value.filter(c => selectedCols.value.includes(c.field)))

function toggleCol(field: string) {
  const idx = selectedCols.value.indexOf(field)
  if (idx >= 0) {
    selectedCols.value.splice(idx, 1)
  } else {
    selectedCols.value.push(field)
  }
}

async function search() {
  try {
    const { data } = await queryCustomDetail(companyId, {
      columns: selectedCols.value,
      filters: filters.value,
      order_by: ['date', 'voucher_no'],
    })
    results.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

async function exportCsv() {
  try {
    const res = await exportCustomDetail(
      companyId,
      filters.value.start_date,
      filters.value.end_date,
      filters.value.account_code || undefined,
    )
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'custom_detail.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '导出失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

onMounted(async () => {
  const { data } = await getCustomDetailColumns()
  columns.value = data
})
</script>
