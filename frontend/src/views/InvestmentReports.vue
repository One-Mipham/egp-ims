<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import { getPositionsReport, getIncomeReport, getFairValueReport } from '@/api'

const activeReport = ref<'positions' | 'income' | 'fair_value'>('positions')
const typeFilter = ref<string | null>(null)
const startDate = ref('')
const endDate = ref('')
const loading = ref(false)
const positionsData = ref<any[]>([])
const incomeData = ref<any>({ items: [], summary_by_type: [], total: 0 })
const fairValueData = ref<any>({ items: [], total_change: 0 })
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const INVEST_TYPES = [
  { label: '全部类型', value: null },
  { label: 'VC', value: 'vc' },
  { label: 'PE', value: 'pe' },
  { label: '一般股权', value: 'general_equity' },
  { label: '二级市场', value: 'secondary_market' },
  { label: '另类资产', value: 'alternative' },
]

async function loadPositions() {
  loading.value = true
  try {
    const res = await getPositionsReport(companyId.value, typeFilter.value || undefined)
    positionsData.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadIncome() {
  loading.value = true
  try {
    const res = await getIncomeReport(companyId.value, startDate.value || undefined, endDate.value || undefined)
    incomeData.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadFairValue() {
  loading.value = true
  try {
    const res = await getFairValueReport(companyId.value, startDate.value || undefined, endDate.value || undefined)
    fairValueData.value = res.data
  } finally {
    loading.value = false
  }
}

function switchReport(r: 'positions' | 'income' | 'fair_value') {
  activeReport.value = r
  if (r === 'positions') loadPositions()
  else if (r === 'income') loadIncome()
  else loadFairValue()
}

onMounted(() => loadPositions())
</script>

<template>
  <div>
    <div class="flex gap-2 mb-4">
      <Button
        :label="'持仓报告'"
        :outlined="activeReport !== 'positions'"
        @click="switchReport('positions')"
        size="small"
      />
      <Button :label="'收益报告'" :outlined="activeReport !== 'income'" @click="switchReport('income')" size="small" />
      <Button
        :label="'公允价值变动'"
        :outlined="activeReport !== 'fair_value'"
        @click="switchReport('fair_value')"
        size="small"
      />
    </div>

    <!-- Positions Report -->
    <div v-if="activeReport === 'positions'">
      <div class="flex gap-2 items-center mb-3">
        <Dropdown
          v-model="typeFilter"
          :options="INVEST_TYPES"
          optionLabel="label"
          optionValue="value"
          class="w-40"
          @change="loadPositions"
        />
        <Button label="刷新" icon="pi pi-refresh" text size="small" @click="loadPositions" />
      </div>

      <DataTable :value="positionsData" :loading="loading" stripedRows size="small">
        <Column field="portfolio_name" header="组合" sortable />
        <Column field="investment_type" header="类型" sortable style="width: 80px">
          <template #body="{ data }"><Tag :value="data.investment_type" /></template>
        </Column>
        <Column field="security_name" header="标的" sortable />
        <Column field="account_code" header="科目" sortable style="width: 80px" />
        <Column field="cost_amount" header="成本" sortable style="width: 120px">
          <template #body="{ data }">{{ data.cost_amount.toLocaleString() }}</template>
        </Column>
        <Column field="fair_value" header="公允价值" sortable style="width: 120px">
          <template #body="{ data }">{{ data.fair_value.toLocaleString() }}</template>
        </Column>
        <Column header="未实现损益" sortable style="width: 140px">
          <template #body="{ data }">
            <div class="flex items-center gap-1">
              <span :class="data.unrealized_gl >= 0 ? 'text-green-600' : 'text-red-600'">{{
                data.unrealized_gl.toLocaleString()
              }}</span>
              <span class="text-xs" :class="data.unrealized_gl_pct >= 0 ? 'text-green-500' : 'text-red-500'"
                >({{ data.unrealized_gl_pct }}%)</span
              >
            </div>
          </template>
        </Column>
        <Column field="fair_value_date" header="估值日" sortable style="width: 100px" />
      </DataTable>
    </div>

    <!-- Income Report -->
    <div v-if="activeReport === 'income'">
      <div class="flex gap-2 items-center mb-3">
        <InputText v-model="startDate" placeholder="开始日期" class="w-36" />
        <InputText v-model="endDate" placeholder="结束日期" class="w-36" />
        <Button label="查询" icon="pi pi-search" size="small" @click="loadIncome" />
      </div>

      <div class="grid grid-cols-4 gap-3 mb-3">
        <Card v-for="s in incomeData.summary_by_type" :key="s.income_type">
          <template #content>
            <div class="text-center">
              <div class="text-xs text-zinc-500">{{ s.income_type }}</div>
              <div class="text-lg font-semibold">{{ s.amount.toLocaleString() }}</div>
            </div>
          </template>
        </Card>
        <Card>
          <template #content>
            <div class="text-center">
              <div class="text-xs text-zinc-500">合计</div>
              <div class="text-lg font-semibold" :class="incomeData.total >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ incomeData.total.toLocaleString() }}
              </div>
            </div>
          </template>
        </Card>
      </div>

      <DataTable :value="incomeData.items" :loading="loading" stripedRows size="small">
        <Column field="income_date" header="日期" sortable style="width: 100px" />
        <Column field="income_type" header="类型" sortable style="width: 120px" />
        <Column field="amount" header="金额" sortable style="width: 120px">
          <template #body="{ data }">{{ data.amount.toLocaleString() }}</template>
        </Column>
        <Column field="notes" header="备注" />
      </DataTable>
    </div>

    <!-- Fair Value Report -->
    <div v-if="activeReport === 'fair_value'">
      <div class="flex gap-2 items-center mb-3">
        <InputText v-model="startDate" placeholder="开始日期" class="w-36" />
        <InputText v-model="endDate" placeholder="结束日期" class="w-36" />
        <Button label="查询" icon="pi pi-search" size="small" @click="loadFairValue" />
        <span class="ml-auto text-sm"
          >总变动:
          <span :class="fairValueData.total_change >= 0 ? 'text-green-600' : 'text-red-600'" class="font-semibold">{{
            fairValueData.total_change.toLocaleString()
          }}</span></span
        >
      </div>

      <DataTable :value="fairValueData.items" :loading="loading" stripedRows size="small">
        <Column field="adjustment_date" header="日期" sortable style="width: 100px" />
        <Column field="previous_value" header="调整前" sortable style="width: 120px">
          <template #body="{ data }">{{ data.previous_value.toLocaleString() }}</template>
        </Column>
        <Column field="adjusted_value" header="调整后" sortable style="width: 120px">
          <template #body="{ data }">{{ data.adjusted_value.toLocaleString() }}</template>
        </Column>
        <Column field="change_amount" header="变动额" sortable style="width: 120px">
          <template #body="{ data }">
            <span :class="data.change_amount >= 0 ? 'text-green-600' : 'text-red-600'">{{
              data.change_amount.toLocaleString()
            }}</span>
          </template>
        </Column>
        <Column field="reason" header="原因" />
      </DataTable>
    </div>
  </div>
</template>
