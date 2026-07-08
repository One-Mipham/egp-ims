<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from 'primevue/card'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import { listPortfolios, listPositions, listTransactions, getIncomeReport } from '@/api'
import { useI18n } from '@/i18n'

const router = useRouter()
const { t } = useI18n()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const portfolios = ref<any[]>([])
const positions = ref<any[]>([])
const recentTransactions = ref<any[]>([])
const incomeTotal = ref(0)
const loading = ref(false)

const totalFairValue = computed(() => positions.value.reduce((s, p) => s + (p.fair_value || 0), 0))
const totalCost = computed(() => positions.value.reduce((s, p) => s + (p.cost_amount || 0), 0))
const unrealizedPnL = computed(() => totalFairValue.value - totalCost.value)
const portfolioCount = computed(() => portfolios.value.filter(p => p.status === 'active').length)

const typeDistribution = computed(() => {
  const map: Record<string, number> = {}
  positions.value.forEach(p => {
    const pf = portfolios.value.find(f => f.id === p.portfolio_id)
    const t = pf?.investment_type || 'other'
    map[t] = (map[t] || 0) + (p.fair_value || 0)
  })
  const total = Object.values(map).reduce((s, v) => s + v, 0) || 1
  return Object.entries(map).map(([k, v]) => ({ type: k, value: v, pct: Math.round((v / total) * 100) }))
})

const TYPE_LABELS: Record<string, string> = {
  vc: 'VC',
  pe: 'PE',
  angel: '天使',
  general_equity: '一般股权',
  secondary_market: '二级市场',
  fixed_income: '固定收益',
  mutual_fund: '公募基金',
  private_fund: '私募基金',
  etf: 'ETF',
  alternative: '另类',
  real_estate: '房地产',
  infrastructure: '基础设施',
  private_credit: '私募信贷',
  commodity: '大宗商品',
  digital_asset: '数字资产',
  trust: '信托',
  derivatives: '衍生品',
}

const TXN_LABELS: Record<string, string> = {
  buy: '买入',
  sell: '卖出',
  capital_call: '资本召唤',
  distribution: '分配返还',
  dividend: '分红',
  interest: '利息',
}

const COLORS = [
  '#6366f1',
  '#8b5cf6',
  '#ec4899',
  '#f59e0b',
  '#10b981',
  '#06b6d4',
  '#3b82f6',
  '#ef4444',
  '#84cc16',
  '#f97316',
  '#14b8a6',
  '#a855f7',
  '#e11d48',
  '#0ea5e9',
  '#d946ef',
  '#22c55e',
  '#64748b',
]

function fmt(n: number) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function load() {
  loading.value = true
  try {
    const [pfRes, posRes, txnRes, incRes] = await Promise.all([
      listPortfolios(companyId.value),
      listPositions(companyId.value),
      listTransactions(companyId.value),
      getIncomeReport(companyId.value),
    ])
    portfolios.value = pfRes.data
    positions.value = posRes.data
    recentTransactions.value = txnRes.data.slice(0, 5)
    incomeTotal.value = incRes.data?.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="p-4 space-y-6">
    <h2 class="text-lg font-semibold text-zinc-700">{{ t('investments.title') }}</h2>

    <!-- Summary Cards -->
    <div class="grid grid-cols-4 gap-4">
      <Card class="shadow-sm">
        <template #content>
          <div class="text-sm text-stone-500 mb-1">总公允价值</div>
          <div class="text-2xl font-bold text-stone-800">¥{{ fmt(totalFairValue) }}</div>
          <div class="text-xs text-stone-400 mt-1">{{ portfolioCount }} 个活跃组合</div>
        </template>
      </Card>
      <Card class="shadow-sm">
        <template #content>
          <div class="text-sm text-stone-500 mb-1">总成本</div>
          <div class="text-2xl font-bold text-stone-800">¥{{ fmt(totalCost) }}</div>
          <div class="text-xs text-stone-400 mt-1">{{ positions.length }} 个持仓</div>
        </template>
      </Card>
      <Card class="shadow-sm">
        <template #content>
          <div class="text-sm text-stone-500 mb-1">未实现盈亏</div>
          <div class="text-2xl font-bold" :class="unrealizedPnL >= 0 ? 'text-emerald-600' : 'text-red-500'">
            ¥{{ fmt(unrealizedPnL) }}
          </div>
          <div class="text-xs text-stone-400 mt-1">
            {{ totalCost ? ((unrealizedPnL / totalCost) * 100).toFixed(1) : '0.0' }}%
          </div>
        </template>
      </Card>
      <Card class="shadow-sm">
        <template #content>
          <div class="text-sm text-stone-500 mb-1">累计收益</div>
          <div class="text-2xl font-bold text-indigo-600">¥{{ fmt(incomeTotal) }}</div>
          <div class="text-xs text-stone-400 mt-1">分红+利息+已实现</div>
        </template>
      </Card>
    </div>

    <div class="grid grid-cols-2 gap-6">
      <!-- Portfolio Distribution -->
      <Card class="shadow-sm">
        <template #title><span class="text-base font-semibold text-zinc-700">持仓分布（按类型）</span></template>
        <template #content>
          <div v-if="typeDistribution.length === 0" class="text-sm text-stone-400 py-8 text-center">{{ t('common.noData') }}</div>
          <div v-else class="space-y-3">
            <div v-for="(item, i) in typeDistribution" :key="item.type" class="flex items-center gap-3">
              <span class="text-xs text-stone-500 w-16 text-right">{{ TYPE_LABELS[item.type] || item.type }}</span>
              <div class="flex-1 bg-stone-100 rounded-full h-4 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :style="{ width: item.pct + '%', backgroundColor: COLORS[i % COLORS.length] }"
                />
              </div>
              <span class="text-xs text-stone-500 w-12">{{ item.pct }}%</span>
              <span class="text-xs text-stone-400 w-20 text-right">¥{{ Math.round(item.value).toLocaleString() }}</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Quick Actions -->
      <Card class="shadow-sm">
        <template #title><span class="text-base font-semibold text-zinc-700">快捷操作</span></template>
        <template #content>
          <div class="grid grid-cols-2 gap-3">
            <Button
              :label="t('investments.portfolios')"
              icon="pi pi-folder"
              severity="secondary"
              size="small"
              @click="router.push('/investments/portfolio')"
            />
            <Button
              :label="t('investments.positions')"
              icon="pi pi-list"
              severity="secondary"
              size="small"
              @click="router.push('/investments/positions')"
            />
            <Button
              :label="t('investments.transactions')"
              icon="pi pi-arrow-right-arrow-left"
              severity="secondary"
              size="small"
              @click="router.push('/investments/transactions')"
            />
            <Button
              :label="t('investments.adjustments')"
              icon="pi pi-chart-line"
              severity="secondary"
              size="small"
              @click="router.push('/investments/adjustments')"
            />
            <Button
              :label="t('investments.income')"
              icon="pi pi-dollar"
              severity="secondary"
              size="small"
              @click="router.push('/investments/income')"
            />
            <Button
              :label="t('investments.reports')"
              icon="pi pi-file"
              severity="secondary"
              size="small"
              @click="router.push('/investments/reports')"
            />
          </div>
        </template>
      </Card>
    </div>

    <!-- Recent Transactions -->
    <Card class="shadow-sm">
      <template #title><span class="text-base font-semibold text-zinc-700">最近交易</span></template>
      <template #content>
        <DataTable :value="recentTransactions" :loading="loading" stripedRows size="small">
          <Column field="transaction_date" :header="t('common.date')" sortable />
          <Column :header="t('common.type')">
            <template #body="{ data }">
              <Tag
                :value="TXN_LABELS[data.transaction_type] || data.transaction_type"
                :severity="
                  data.transaction_type === 'buy' ? 'success' : data.transaction_type === 'sell' ? 'danger' : 'info'
                "
                class="text-xs"
              />
            </template>
          </Column>
          <Column field="quantity" header="数量" />
          <Column field="price" header="价格">
            <template #body="{ data }">¥{{ data.price?.toLocaleString() }}</template>
          </Column>
          <Column field="amount" :header="t('common.amount')">
            <template #body="{ data }">¥{{ data.amount?.toLocaleString() }}</template>
          </Column>
          <Column field="notes" :header="t('common.remark')" />
        </DataTable>
        <div v-if="recentTransactions.length === 0 && !loading" class="text-sm text-stone-400 py-4 text-center">
          暂无交易记录
        </div>
      </template>
    </Card>
  </div>
</template>
