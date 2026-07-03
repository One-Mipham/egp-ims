<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Card from 'primevue/card'
import { listPortfolios, getPositionsReport, getIncomeReport } from '@/api'
import api from '@/api/index'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const portfolios = ref<any[]>([])
const selectedPortfolio = ref<number | null>(null)
const startDate = ref('')
const endDate = ref('')
const result = ref<any>(null)
const loading = ref(false)

async function loadPortfolios() {
  try {
    const r = await listPortfolios(companyId.value)
    portfolios.value = r.data
  } catch {}
}

async function runQuery() {
  loading.value = true
  try {
    const r = await api.get('/investments/reports/performance', {
      params: {
        company_id: companyId.value,
        ...(selectedPortfolio.value ? { portfolio_id: selectedPortfolio.value } : {}),
        ...(startDate.value ? { start_date: startDate.value } : {}),
        ...(endDate.value ? { end_date: endDate.value } : {}),
      },
    })
    result.value = r.data
  } finally {
    loading.value = false
  }
}

const CASH_LABELS: Record<string, string> = {
  buy: '买入',
  sell: '卖出',
  capital_call: '资本召唤',
  distribution: '分配返还',
  dividend: '分红',
  interest: '利息',
  realized_gain: '已实现收益',
  fair_value: '期末估值',
}

onMounted(loadPortfolios)
</script>

<template>
  <div class="p-4 space-y-6">
    <h2 class="text-lg font-semibold text-zinc-700">绩效分析</h2>

    <!-- Filters -->
    <div class="flex items-end gap-3 bg-white rounded-lg border border-stone-200 p-4">
      <div>
        <label class="text-xs text-stone-500 block mb-1">投资组合</label
        ><Dropdown
          v-model="selectedPortfolio"
          :options="portfolios"
          optionLabel="name"
          optionValue="id"
          placeholder="全部组合"
          showClear
          class="w-48"
        />
      </div>
      <div>
        <label class="text-xs text-stone-500 block mb-1">起始日</label
        ><InputText v-model="startDate" placeholder="YYYY-MM-DD" class="w-36" />
      </div>
      <div>
        <label class="text-xs text-stone-500 block mb-1">截止日</label
        ><InputText v-model="endDate" placeholder="YYYY-MM-DD" class="w-36" />
      </div>
      <Button label="计算" icon="pi pi-calculator" @click="runQuery" :loading="loading" />
    </div>

    <!-- Results -->
    <div v-if="result" class="space-y-6">
      <div class="grid grid-cols-4 gap-4">
        <Card class="shadow-sm"
          ><template #content
            ><div class="text-sm text-stone-500">MOIC</div>
            <div class="text-2xl font-bold text-indigo-600">{{ result.moic }}x</div>
            <div class="text-xs text-stone-400">投资回报倍数</div></template
          ></Card
        >
        <Card class="shadow-sm"
          ><template #content
            ><div class="text-sm text-stone-500">IRR</div>
            <div class="text-2xl font-bold" :class="result.irr_pct >= 0 ? 'text-emerald-600' : 'text-red-500'">
              {{ result.irr_pct }}%
            </div>
            <div class="text-xs text-stone-400">内部收益率（近似）</div></template
          ></Card
        >
        <Card class="shadow-sm"
          ><template #content
            ><div class="text-sm text-stone-500">总投入成本</div>
            <div class="text-2xl font-bold text-stone-800">¥{{ result.total_cost?.toLocaleString() }}</div></template
          ></Card
        >
        <Card class="shadow-sm"
          ><template #content
            ><div class="text-sm text-stone-500">回收+收益+期末FV</div>
            <div class="text-2xl font-bold text-stone-800">
              ¥{{ (result.total_proceeds + result.total_income + result.current_fair_value)?.toLocaleString() }}
            </div></template
          ></Card
        >
      </div>

      <!-- Cash Flows -->
      <div class="bg-white rounded-lg border border-stone-200 p-4">
        <h3 class="font-semibold text-zinc-700 mb-3">现金流明细 ({{ result.cash_flows?.length || 0 }} 笔)</h3>
        <DataTable :value="result.cash_flows" stripedRows size="small">
          <Column field="date" header="日期" sortable />
          <Column header="类型"
            ><template #body="{ data }"
              ><span class="text-sm">{{ CASH_LABELS[data.label] || data.label }}</span></template
            ></Column
          >
          <Column header="金额">
            <template #body="{ data }">
              <span :class="data.amount >= 0 ? 'text-emerald-600' : 'text-red-500'">
                {{ data.amount >= 0 ? '+' : '' }}¥{{ Math.abs(data.amount).toLocaleString() }}
              </span>
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <div v-else class="text-sm text-stone-400 py-8 text-center">选择筛选条件后点击「计算」查看绩效指标</div>
  </div>
</template>
