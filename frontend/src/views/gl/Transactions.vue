<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">往来管理</h2>

    <TabView v-model:activeIndex="activeTab">
      <TabPanel header="余额汇总" value="0">
        <div class="flex gap-2 items-end mb-3">
          <div>
            <label class="text-xs block mb-1">{{ t('accounting.gl_page.startPeriod') }}</label>
            <InputText v-model="filters.start_period" size="small" placeholder="yyyy-MM" class="w-32" />
          </div>
          <div>
            <label class="text-xs block mb-1">{{ t('accounting.gl_page.endPeriod') }}</label>
            <InputText v-model="filters.end_period" size="small" placeholder="yyyy-MM" class="w-32" />
          </div>
          <div>
            <label class="text-xs block mb-1">{{ t('accounting.gl_page.accountCode') }}</label>
            <InputText v-model="filters.account_code" size="small" placeholder="如 1122" class="w-28" />
          </div>
          <Button :label="t('common.search')" icon="pi pi-search" size="small" @click="loadBalances" />
        </div>
        <DataTable :value="balances" stripedRows @row-click="drillDown">
          <Column field="counterparty_name" :header="t('accounting.gl_page.counterparty')" />
          <Column field="beginning_balance" :header="t('accounting.gl_page.beginningBalance')" style="width: 8rem">
            <template #body="{ data }">{{ data.beginning_balance.toLocaleString() }}</template>
          </Column>
          <Column field="current_debit" :header="t('accounting.gl_page.currentPeriodDebit')" style="width: 8rem">
            <template #body="{ data }">{{ data.current_debit.toLocaleString() }}</template>
          </Column>
          <Column field="current_credit" :header="t('accounting.gl_page.currentPeriodCredit')" style="width: 8rem">
            <template #body="{ data }">{{ data.current_credit.toLocaleString() }}</template>
          </Column>
          <Column field="ending_balance" :header="t('accounting.gl_page.endingBalance')" style="width: 8rem">
            <template #body="{ data }">
              <span :class="data.direction === 'debit' ? 'text-blue-600' : 'text-red-600'">
                {{ data.direction === 'debit' ? '借' : '贷' }} {{ data.ending_balance.toLocaleString() }}
              </span>
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <TabPanel header="往来明细" value="1">
        <div class="flex gap-2 items-end mb-3">
          <div>
            <label class="text-xs block mb-1">往来单位</label>
            <Dropdown
              v-model="detailFilters.counterparty_id"
              :options="balanceOptions"
              optionLabel="counterparty_name"
              optionValue="counterparty_id"
              filter
              placeholder="选择"
              class="w-48"
            />
          </div>
          <div>
            <label class="text-xs block mb-1">{{ t('accounting.gl_page.startPeriod') }}</label>
            <InputText v-model="detailFilters.start_period" size="small" class="w-28" />
          </div>
          <div>
            <label class="text-xs block mb-1">{{ t('accounting.gl_page.endPeriod') }}</label>
            <InputText v-model="detailFilters.end_period" size="small" class="w-28" />
          </div>
          <Button
            :label="t('common.search')"
            icon="pi pi-search"
            size="small"
            @click="loadDetail"
            :disabled="!detailFilters.counterparty_id"
          />
        </div>
        <DataTable v-if="detail" :value="detail.entries" stripedRows size="small">
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
            <template #body="{ data }">{{ data.balance.toLocaleString() }}</template>
          </Column>
        </DataTable>
      </TabPanel>

      <TabPanel :header="t('accounting.gl_page.aging')" value="2">
        <div class="flex gap-2 items-end mb-3">
          <div>
            <label class="text-xs block mb-1">{{ t('accounting.gl_page.endPeriod') }}</label>
            <InputText v-model="agingFilters.end_period" size="small" class="w-32" />
          </div>
          <Button :label="t('common.search')" icon="pi pi-search" size="small" @click="loadAging" />
        </div>
        <DataTable :value="aging" stripedRows>
          <Column field="counterparty_name" :header="t('accounting.gl_page.counterparty')" />
          <Column field="total_balance" header="总余额" style="width: 8rem">
            <template #body="{ data }">{{ data.total_balance.toLocaleString() }}</template>
          </Column>
          <Column v-for="b in agingBuckets" :key="b" :header="b" style="width: 7rem">
            <template #body="{ data }">
              {{ data.buckets?.find((x: any) => x.range === b)?.amount?.toLocaleString() || '' }}
            </template>
          </Column>
        </DataTable>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from '@/i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import { getTransactionBalances, getTransactionDetail, getTransactionAging } from '../../api'

const toast = useToast()
const { t } = useI18n()
const companyId = Number(localStorage.getItem('company_id') || '1')
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const activeTab = ref(0)
const agingBuckets = ['0-30天', '31-90天', '91-180天', '181-365天', '365天+']

const filters = ref({
  start_period: defaultPeriod,
  end_period: defaultPeriod,
  account_code: '',
})

const balances = ref<any[]>([])
const detail = ref<any>(null)
const aging = ref<any[]>([])

const detailFilters = ref({
  counterparty_id: null as number | null,
  start_period: defaultPeriod,
  end_period: defaultPeriod,
})

const agingFilters = ref({ end_period: defaultPeriod })

const balanceOptions = computed(() =>
  balances.value.map(b => ({ counterparty_id: b.counterparty_id, counterparty_name: b.counterparty_name })),
)

async function loadBalances() {
  try {
    const { data } = await getTransactionBalances(
      companyId,
      filters.value.start_period,
      filters.value.end_period,
      filters.value.account_code || undefined,
    )
    balances.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

function drillDown(e: any) {
  detailFilters.value.counterparty_id = e.data.counterparty_id
  activeTab.value = 1
  loadDetail()
}

async function loadDetail() {
  if (!detailFilters.value.counterparty_id) return
  try {
    const { data } = await getTransactionDetail(
      companyId,
      detailFilters.value.counterparty_id,
      detailFilters.value.start_period,
      detailFilters.value.end_period,
    )
    detail.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

async function loadAging() {
  try {
    const { data } = await getTransactionAging(companyId, agingFilters.value.end_period)
    aging.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

loadBalances()
</script>
