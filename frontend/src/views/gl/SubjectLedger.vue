<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">科目账</h2>

    <div class="flex gap-3 items-end mb-4 flex-wrap">
      <div>
        <label class="block text-sm mb-1">{{ t('accounting.gl_page.accountCode') }}</label>
        <InputText v-model="filters.account_code" placeholder="如 1001 或 660" />
      </div>
      <div>
        <label class="block text-sm mb-1">级别</label>
        <Dropdown v-model="filters.level" :options="[null, 1, 2, 3, 4]" class="w-24">
          <template #value="slotProps">{{ slotProps.value ? slotProps.value + '级' : '全部' }}</template>
          <template #option="slotProps">{{ slotProps.option ? slotProps.option + '级' : '全部' }}</template>
        </Dropdown>
      </div>
      <div>
        <label class="block text-sm mb-1">{{ t('accounting.gl_page.startPeriod') }}</label>
        <InputText v-model="filters.start_period" placeholder="yyyy-MM" />
      </div>
      <div>
        <label class="block text-sm mb-1">{{ t('accounting.gl_page.endPeriod') }}</label>
        <InputText v-model="filters.end_period" placeholder="yyyy-MM" />
      </div>
      <div class="flex items-center gap-2">
        <Checkbox v-model="filters.include_zero" :binary="true" inputId="include_zero" />
        <label for="include_zero">含无发生额</label>
      </div>
      <Button :label="t('common.search')" icon="pi pi-search" @click="search" />
    </div>

    <Accordion :activeIndex="activeIndex" v-if="results.length">
      <AccordionTab v-for="(item, i) in results" :key="i">
        <template #header>
          <div class="flex justify-between w-full pr-4">
            <span
              ><strong>{{ item.account_code }}</strong> {{ item.account_name }}</span
            >
            <span class="text-sm"
              >期初: {{ item.beginning_balance.toLocaleString() }} | 借: {{ item.total_debit.toLocaleString() }} | 贷:
              {{ item.total_credit.toLocaleString() }} | 期末: {{ item.ending_balance.toLocaleString() }}</span
            >
          </div>
        </template>
        <DataTable :value="item.entries" size="small" stripedRows>
          <Column field="date" :header="t('common.date')" style="width: 7rem" />
          <Column field="voucher_no" header="凭证号" style="width: 7rem" />
          <Column field="summary" header="摘要" />
          <Column field="debit" header="借方" style="width: 8rem">
            <template #body="{ data }">{{ data.debit ? data.debit.toLocaleString() : '' }}</template>
          </Column>
          <Column field="credit" header="贷方" style="width: 8rem">
            <template #body="{ data }">{{ data.credit ? data.credit.toLocaleString() : '' }}</template>
          </Column>
          <Column field="balance" :header="t('accounting.gl_page.balance')" style="width: 8rem">
            <template #body="{ data }">{{ data.balance.toLocaleString() }}</template>
          </Column>
        </DataTable>
      </AccordionTab>
    </Accordion>
    <div v-else-if="searched" class="text-center text-gray-400 py-8">无查询结果</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from '@/i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import { getSubjectLedger } from '../../api'

const toast = useToast()
const { t } = useI18n()
const companyId = Number(localStorage.getItem('companyId') || '1')
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const filters = ref({
  account_code: '',
  level: null as number | null,
  start_period: defaultPeriod,
  end_period: defaultPeriod,
  include_zero: false,
})

const results = ref<any[]>([])
const searched = ref(false)
const activeIndex = ref<number | null>(null)

async function search() {
  try {
    const { data } = await getSubjectLedger(companyId, filters.value.start_period, filters.value.end_period, {
      account_code: filters.value.account_code || undefined,
      level: filters.value.level || undefined,
      include_zero: filters.value.include_zero,
    })
    results.value = data
    searched.value = true
    activeIndex.value = 0
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}
</script>
