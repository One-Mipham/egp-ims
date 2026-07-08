<script setup lang="ts">
import { reactive, computed, ref, onMounted } from 'vue'
import { listBudgets, getBudget, createBudget, updateBudget, type BudgetData } from '@/api/budget'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const currentYear = new Date().getFullYear()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const futureYears = computed(() => [`${currentYear + 1}年`, `${currentYear + 2}年`, `${currentYear + 3}年`])

// ── Manual input data (12 months each) ──
const data = reactive({
  revenue: Array(12).fill(null) as (number | null)[],
  cost: Array(12).fill(null) as (number | null)[],
  operatingExp: Array(12).fill(null) as (number | null)[],
  adminExp: Array(12).fill(null) as (number | null)[],
  financeExp: Array(12).fill(null) as (number | null)[],
  otherIncExp: Array(12).fill(null) as (number | null)[],
  incomeTax: Array(12).fill(null) as (number | null)[],
})

// ── Budget identification ──
const budgetId = ref<number | null>(null)
const budgetName = ref(`年预算`)
const budgetStatus = ref('draft')

// ── Growth rate & manual adjustment ──
const revenueGrowthRate = ref<number | null>(null) // 百分比 (e.g. 15 = 15%)
const manualAdjustment = ref<number | null>(null) // 手动调整额（可为负数）

// Auto-computed future year revenue (compound growth + yearly adjustment accumulation)
const autoRevenueY1 = computed(() => {
  const base = annualSum(data.revenue)
  if (base == null) return null
  const r = (revenueGrowthRate.value ?? 0) / 100
  const adj = manualAdjustment.value ?? 0
  return parseFloat((base * (1 + r) + adj).toFixed(2))
})
const autoRevenueY2 = computed(() => {
  const base = annualSum(data.revenue)
  if (base == null) return null
  const r = (revenueGrowthRate.value ?? 0) / 100
  const adj = manualAdjustment.value ?? 0
  return parseFloat((base * Math.pow(1 + r, 2) + adj * 2).toFixed(2))
})
const autoRevenueY3 = computed(() => {
  const base = annualSum(data.revenue)
  if (base == null) return null
  const r = (revenueGrowthRate.value ?? 0) / 100
  const adj = manualAdjustment.value ?? 0
  return parseFloat((base * Math.pow(1 + r, 3) + adj * 3).toFixed(2))
})

// ── Auto-computed cost/expense for future years based on ratio settings ──
const costRate = ref<number | null>(null)
const operatingExpRate = ref<number | null>(null)
const adminExpRate = ref<number | null>(null)
const financeExpRate = ref<number | null>(null)

// Auto-fill defaults for future year values (can be manually overridden)
const autoYearDefaults = computed(() => {
  const rev = [autoRevenueY1.value, autoRevenueY2.value, autoRevenueY3.value]
  return {
    cost: rev.map(v => v != null && costRate.value != null ? parseFloat((v * costRate.value / 100).toFixed(2)) : null),
    operatingExp: rev.map(v => v != null && operatingExpRate.value != null ? parseFloat((v * operatingExpRate.value / 100).toFixed(2)) : null),
    adminExp: rev.map(v => v != null && adminExpRate.value != null ? parseFloat((v * adminExpRate.value / 100).toFixed(2)) : null),
    financeExp: rev.map(v => v != null && financeExpRate.value != null ? parseFloat((v * financeExpRate.value / 100).toFixed(2)) : null),
  }
})

// Get default value for a future year cell (auto-computed but can be overridden manually)
function getYearDefault(key: string, yi: number): number | null {
  switch (key) {
    case 'cost': return autoYearDefaults.value.cost[yi]
    case 'operatingExp': return autoYearDefaults.value.operatingExp[yi]
    case 'adminExp': return autoYearDefaults.value.adminExp[yi]
    case 'financeExp': return autoYearDefaults.value.financeExp[yi]
    default: return null
  }
}

const manualKeys = ['revenue', 'cost', 'operatingExp', 'adminExp', 'financeExp', 'otherIncExp', 'incomeTax'] as const

function setValue(key: (typeof manualKeys)[number], monthIdx: number, val: string) {
  const n = parseFloat(val)
  ;(data[key] as (number | null)[])[monthIdx] = isNaN(n) ? null : n
}

// ── Future year annual planning (manual for non-revenue) ──
const yearData = reactive<Record<(typeof manualKeys)[number], (number | null)[]>>({
  revenue: [null, null, null],
  cost: [null, null, null],
  operatingExp: [null, null, null],
  adminExp: [null, null, null],
  financeExp: [null, null, null],
  otherIncExp: [null, null, null],
  incomeTax: [null, null, null],
})

function setYearValue(key: (typeof manualKeys)[number], yi: number, val: string) {
  const n = parseFloat(val)
  yearData[key][yi] = isNaN(n) ? null : n
}

// Auto-computed next year values
const yearGrossProfit = computed(() =>
  yearData.revenue.map((v, i) => (v != null && yearData.cost[i] != null ? v - yearData.cost[i]! : null)),
)
const yearGrossMargin = computed(() =>
  yearGrossProfit.value.map((v, i) =>
    v != null && yearData.revenue[i] != null && yearData.revenue[i] !== 0
      ? parseFloat(((v / yearData.revenue[i]!) * 100).toFixed(1))
      : null,
  ),
)
const yearPeriodExp = computed(() =>
  yearData.revenue.map((_, i) => {
    const o = yearData.operatingExp[i]
    const a = yearData.adminExp[i]
    const f = yearData.financeExp[i]
    if (o == null && a == null && f == null) return null
    return (o ?? 0) + (a ?? 0) + (f ?? 0)
  }),
)
const yearPretaxProfit = computed(() =>
  yearGrossProfit.value.map((v, i) => {
    if (v == null && yearPeriodExp.value[i] == null && yearData.otherIncExp[i] == null) return null
    return (v ?? 0) - (yearPeriodExp.value[i] ?? 0) + (yearData.otherIncExp[i] ?? 0)
  }),
)
const yearNetProfit = computed(() =>
  yearPretaxProfit.value.map((v, i) =>
    v != null && yearData.incomeTax[i] != null ? v - yearData.incomeTax[i]! : null,
  ),
)

// Get the auto-computed revenue for future year yi (0=Y+1, 1=Y+2, 2=Y+3)
function getAutoRevenue(yi: number): number | null {
  if (yi === 0) return autoRevenueY1.value
  if (yi === 1) return autoRevenueY2.value
  return autoRevenueY3.value
}

function getYearValue(label: string, yi: number): number | null {
  switch (label) {
    case '收入':
      return getAutoRevenue(yi) // Always auto-computed from growth rate
    case '成本': {
      const manual = yearData.cost[yi]
      if (manual != null) return manual  // manual override
      return getYearDefault('cost', yi)  // auto-computed default
    }
    case '毛利润':
      return yearGrossProfit.value[yi]
    case '毛利率':
      return yearGrossMargin.value[yi]
    case '经营费用': {
      const manual = yearData.operatingExp[yi]
      return manual != null ? manual : getYearDefault('operatingExp', yi)
    }
    case '管理费用': {
      const manual = yearData.adminExp[yi]
      return manual != null ? manual : getYearDefault('adminExp', yi)
    }
    case '财务费用': {
      const manual = yearData.financeExp[yi]
      return manual != null ? manual : getYearDefault('financeExp', yi)
    }
    case '期间费用合计':
      return yearPeriodExp.value[yi]
    case '营业外收支':
      return yearData.otherIncExp[yi]
    case '税前利润':
      return yearPretaxProfit.value[yi]
    case '所得税':
      return yearData.incomeTax[yi]
    case '税后利润':
      return yearNetProfit.value[yi]
    default:
      return null
  }
}
function getYearInputKey(label: string): (typeof manualKeys)[number] | null {
  switch (label) {
    case '收入':
      return null // Revenue is auto-computed, not manual
    case '成本':
      return 'cost'
    case '经营费用':
      return 'operatingExp'
    case '管理费用':
      return 'adminExp'
    case '财务费用':
      return 'financeExp'
    case '营业外收支':
      return 'otherIncExp'
    case '所得税':
      return 'incomeTax'
    default:
      return null
  }
}

// ── Auto-computed rows (12-month arrays) ──
const grossProfit = computed(() =>
  data.revenue.map((v, i) => (v != null && data.cost[i] != null ? v - data.cost[i]! : null)),
)
const grossMargin = computed(() =>
  grossProfit.value.map((v, i) =>
    v != null && data.revenue[i] != null && data.revenue[i] !== 0
      ? parseFloat(((v / data.revenue[i]!) * 100).toFixed(1))
      : null,
  ),
)
const periodExp = computed(() =>
  data.revenue.map((_, i) => {
    const o = data.operatingExp[i]
    const a = data.adminExp[i]
    const f = data.financeExp[i]
    if (o == null && a == null && f == null) return null
    return (o ?? 0) + (a ?? 0) + (f ?? 0)
  }),
)
const pretaxProfit = computed(() =>
  grossProfit.value.map((v, i) => {
    if (v == null && periodExp.value[i] == null && data.otherIncExp[i] == null) return null
    return (v ?? 0) - (periodExp.value[i] ?? 0) + (data.otherIncExp[i] ?? 0)
  }),
)
const netProfit = computed(() =>
  pretaxProfit.value.map((v, i) => (v != null && data.incomeTax[i] != null ? v - data.incomeTax[i]! : null)),
)

// ── Quarterly & annual helpers ──
function qSum(values: (number | null)[], q: number): number | null {
  const start = (q - 1) * 3
  const slice = values.slice(start, start + 3)
  if (slice.every(v => v == null)) return null
  return slice.reduce((a: number, v) => a + (v ?? 0), 0)
}

function annualSum(values: (number | null)[]): number | null {
  if (values.every(v => v == null)) return null
  return values.reduce((a: number, v) => a + (v ?? 0), 0)
}

function fmt(v: number | null): string {
  if (v == null) return ''
  return v.toLocaleString()
}

function fmtPct(v: number | null): string {
  if (v == null) return ''
  return v.toFixed(1) + '%'
}

// Row definitions
interface TableRow {
  label: string
  type: 'manual' | 'auto'
  indent?: boolean
  bold?: boolean
  getValue: (i: number) => number | null
  format?: (v: number | null) => string
}

const tableRows = computed<TableRow[]>(() => [
  { label: '收入', type: 'manual', bold: true, getValue: i => data.revenue[i], format: fmt },
  { label: '成本', type: 'manual', indent: true, getValue: i => data.cost[i], format: fmt },
  { label: '毛利润', type: 'auto', bold: true, getValue: i => grossProfit.value[i], format: fmt },
  { label: '毛利率', type: 'auto', getValue: i => grossMargin.value[i], format: fmtPct },
  { label: '经营费用', type: 'manual', indent: true, getValue: i => data.operatingExp[i], format: fmt },
  { label: '管理费用', type: 'manual', indent: true, getValue: i => data.adminExp[i], format: fmt },
  { label: '财务费用', type: 'manual', indent: true, getValue: i => data.financeExp[i], format: fmt },
  { label: '期间费用合计', type: 'auto', bold: true, getValue: i => periodExp.value[i], format: fmt },
  { label: '营业外收支', type: 'manual', getValue: i => data.otherIncExp[i], format: fmt },
  { label: '税前利润', type: 'auto', bold: true, getValue: i => pretaxProfit.value[i], format: fmt },
  { label: '所得税', type: 'manual', indent: true, getValue: i => data.incomeTax[i], format: fmt },
  { label: '税后利润', type: 'auto', bold: true, getValue: i => netProfit.value[i], format: fmt },
])

function getRowValues(row: TableRow, mi: number): number | null {
  return row.getValue(mi)
}

const quarters = ['Q1小计', 'Q2小计', 'Q3小计', 'Q4小计']
const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

// ── Budget completion analysis ──
const actualRevenue = Array(12).fill(null)
const actualNetProfit = Array(12).fill(null)

const revenueCompletion = computed(() => {
  const actual = annualSum(actualRevenue)
  const budget = annualSum(data.revenue)
  if (actual == null || budget == null || budget === 0) return null
  return parseFloat(((actual / budget) * 100).toFixed(1))
})

const profitCompletion = computed(() => {
  const actual = annualSum(actualNetProfit)
  const budget = annualSum(netProfit.value)
  if (actual == null || budget == null || budget === 0) return null
  return parseFloat(((actual / budget) * 100).toFixed(1))
})

// ── API persistence ──
const saving = ref(false)
const loading = ref(false)
const saveMessage = ref('')
const saveError = ref(false)

function buildBudgetItems(): { account_code: string; month: string; amount: number }[] {
  const items: { account_code: string; month: string; amount: number }[] = []
  const rowMap: Record<string, (number | null)[]> = {
    revenue: data.revenue,
    cost: data.cost,
    operatingExp: data.operatingExp,
    adminExp: data.adminExp,
    financeExp: data.financeExp,
    otherIncExp: data.otherIncExp,
    incomeTax: data.incomeTax,
  }
  for (const [key, values] of Object.entries(rowMap)) {
    for (let mi = 0; mi < 12; mi++) {
      if (values[mi] != null) {
        const monthStr = `${currentYear}-${String(mi + 1).padStart(2, '0')}`
        items.push({ account_code: key, month: monthStr, amount: values[mi]! })
      }
    }
  }
  return items
}

function loadFromItems(items: { account_code: string; month: string; amount: number }[]) {
  // Clear all data first
  for (const key of manualKeys) {
    ;(data[key] as (number | null)[]).fill(null)
  }
  // Load from items
  for (const item of items) {
    const monthIdx = parseInt(item.month.slice(5, 7)) - 1
    if (monthIdx >= 0 && monthIdx < 12) {
      const key = item.account_code as (typeof manualKeys)[number]
      if (manualKeys.includes(key)) {
        ;(data[key] as (number | null)[])[monthIdx] = item.amount
      }
    }
  }
}

async function saveBudget() {
  saving.value = true
  saveMessage.value = ''
  try {
    const items = buildBudgetItems()
    const payload: Record<string, any> = {
      company_id: companyId.value,
      name: budgetName.value,
      year: currentYear,
      items,
      revenue_growth_rate: revenueGrowthRate.value,
      manual_adjustment: manualAdjustment.value,
      cost_rate: costRate.value,
      operating_exp_rate: operatingExpRate.value,
      admin_exp_rate: adminExpRate.value,
      finance_exp_rate: financeExpRate.value,
    }
    if (budgetId.value) {
      await updateBudget(budgetId.value, payload)
    } else {
      const res = await createBudget(payload as any)
      budgetId.value = (res.data as BudgetData).id
    }
    saveMessage.value = t('common.saveSuccess')
    saveError.value = false
  } catch (e: any) {
    saveMessage.value = t('common.saveFailed') + ': ' + (e?.response?.data?.detail || e.message)
    saveError.value = true
  } finally {
    saving.value = false
  }
}

async function loadBudget() {
  loading.value = true
  try {
    const res = await listBudgets(companyId.value, currentYear)
    const list = res.data as any[]
    if (list.length > 0) {
      const detail = await getBudget(list[0].id)
      const budget = detail.data as any
      budgetId.value = budget.id
      budgetName.value = budget.name
      budgetStatus.value = budget.status
      revenueGrowthRate.value = budget.revenue_growth_rate ?? null
      manualAdjustment.value = budget.manual_adjustment ?? null
      costRate.value = budget.cost_rate ?? null
      operatingExpRate.value = budget.operating_exp_rate ?? null
      adminExpRate.value = budget.admin_exp_rate ?? null
      financeExpRate.value = budget.finance_exp_rate ?? null
      loadFromItems(budget.items || [])
    }
  } catch (_e) {
    // No saved budget exists yet — that's fine
  } finally {
    loading.value = false
  }
}

function exportBudget() {
  const rows = ['项目,' + months.join(',') + ',Q1小计,Q2小计,Q3小计,Q4小计,年度合计']
  for (const row of tableRows.value) {
    const yearVals = months.map((_, i) => row.getValue(i))
    const cells = [row.label]
    for (let i = 0; i < 12; i++) cells.push(yearVals[i] != null ? yearVals[i]!.toLocaleString() : '')
    for (let q = 1; q <= 4; q++) cells.push(fmt(qSum(yearVals, q)))
    cells.push(fmt(annualSum(yearVals)))
    rows.push(cells.join(','))
  }
  const blob = new Blob(['﻿' + rows.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `预算_${currentYear}.csv`; a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadBudget()
})
</script>

<template>
  <div class="space-y-6">
    <div class="page-header flex items-center justify-between">
      <h2>{{ t('finance.budget_page.title') }}</h2>
      <div class="flex items-center gap-2">
        <span
          v-if="saveMessage"
          class="text-xs"
          :class="saveError ? 'text-red-500' : 'text-green-600'"
          >{{ saveMessage }}</span
        >
        <button
          class="px-3 py-1 text-xs border border-stone-300 rounded hover:bg-stone-100 disabled:opacity-50"
          :disabled="loading"
          @click="loadBudget"
        >
          {{ loading ? t('common.loading') : t('finance.budget_page.loadBudget') }}
        </button>
        <button
          class="px-3 py-1 text-xs bg-amber-500 text-white rounded hover:bg-amber-600 disabled:opacity-50"
          :disabled="saving"
          @click="saveBudget"
        >
          {{ saving ? t('common.loading') : t('finance.budget_page.saveBudget') }}
        </button>
        <button class="px-3 py-1 text-xs bg-stone-500 text-white rounded hover:bg-stone-600" @click="exportBudget">
          {{ t('finance.budget_page.exportCSV') }}
        </button>
      </div>
    </div>

    <!-- ═══════════ 增长率与调整设置 ═══════════ -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">{{ t('finance.budget_page.growthRateSettings') }}</h3>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs text-stone-500 mb-1">{{ t('finance.budget_page.revenueGrowthRate') }}</label>
          <div class="flex items-center gap-1">
            <input
              type="number"
              step="0.1"
              class="w-24 px-2 py-1 border border-stone-300 rounded text-sm font-number focus:border-amber-400 focus:outline-none"
              :value="revenueGrowthRate != null ? revenueGrowthRate : ''"
              placeholder="如 15"
              @input="
                (e: Event) => {
                  const v = parseFloat((e.target as HTMLInputElement).value)
                  revenueGrowthRate = isNaN(v) ? null : v
                }
              "
            />
            <span class="text-xs text-stone-400">%</span>
          </div>
          <p class="text-[10px] text-stone-400 mt-1">设定目标增长率，未来三年收入自动计算</p>
        </div>
        <div>
          <label class="block text-xs text-stone-500 mb-1">{{ t('finance.budget_page.manualAdjustment') }}</label>
          <div class="flex items-center gap-1">
            <input
              type="number"
              step="0.01"
              class="w-32 px-2 py-1 border border-stone-300 rounded text-sm font-number focus:border-amber-400 focus:outline-none"
              :value="manualAdjustment != null ? manualAdjustment : ''"
              placeholder="可为负数"
              @input="
                (e: Event) => {
                  const v = parseFloat((e.target as HTMLInputElement).value)
                  manualAdjustment = isNaN(v) ? null : v
                }
              "
            />
          </div>
          <p class="text-[10px] text-stone-400 mt-1">对未来每年收入统一增减额（负数表示调减）</p>
        </div>
        <div>
          <label class="block text-xs text-stone-500 mb-1">{{ t('finance.budget_page.costRate') }}</label>
          <div class="flex items-center gap-1">
            <input type="number" step="0.1" class="w-24 px-2 py-1 border border-stone-300 rounded text-sm font-number focus:border-amber-400 focus:outline-none"
              :value="costRate != null ? costRate : ''" placeholder="如 60"
              @input="(e: Event) => { const v = parseFloat((e.target as HTMLInputElement).value); costRate = isNaN(v) ? null : v }" />
            <span class="text-xs text-stone-400">%</span>
          </div>
        </div>
        <div>
          <label class="block text-xs text-stone-500 mb-1">{{ t('finance.budget_page.operatingExpRate') }}</label>
          <div class="flex items-center gap-1">
            <input type="number" step="0.1" class="w-24 px-2 py-1 border border-stone-300 rounded text-sm font-number focus:border-amber-400 focus:outline-none"
              :value="operatingExpRate != null ? operatingExpRate : ''" placeholder="如 10"
              @input="(e: Event) => { const v = parseFloat((e.target as HTMLInputElement).value); operatingExpRate = isNaN(v) ? null : v }" />
            <span class="text-xs text-stone-400">%</span>
          </div>
        </div>
        <div>
          <label class="block text-xs text-stone-500 mb-1">{{ t('finance.budget_page.adminExpRate') }}</label>
          <div class="flex items-center gap-1">
            <input type="number" step="0.1" class="w-24 px-2 py-1 border border-stone-300 rounded text-sm font-number focus:border-amber-400 focus:outline-none"
              :value="adminExpRate != null ? adminExpRate : ''" placeholder="如 15"
              @input="(e: Event) => { const v = parseFloat((e.target as HTMLInputElement).value); adminExpRate = isNaN(v) ? null : v }" />
            <span class="text-xs text-stone-400">%</span>
          </div>
        </div>
        <div>
          <label class="block text-xs text-stone-500 mb-1">{{ t('finance.budget_page.financeExpRate') }}</label>
          <div class="flex items-center gap-1">
            <input type="number" step="0.1" class="w-24 px-2 py-1 border border-stone-300 rounded text-sm font-number focus:border-amber-400 focus:outline-none"
              :value="financeExpRate != null ? financeExpRate : ''" placeholder="如 3"
              @input="(e: Event) => { const v = parseFloat((e.target as HTMLInputElement).value); financeExpRate = isNaN(v) ? null : v }" />
            <span class="text-xs text-stone-400">%</span>
          </div>
        </div>
      </div>
      <p class="text-[10px] text-stone-400 mt-3">{{ t('finance.budget_page.autoComputeHint') }}</p>
    </div>

    <!-- ═══════════ 年度预算表 ═══════════ -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">年度预算表</h3>
      <p class="text-[10px] text-stone-400 mb-2">
        月度数据手工填入；季度小计、年度合计及粗体行（毛利润、毛利率、期间费用合计、税前利润、税后利润）为自动计算。
        未来三年收入由增长率与调整额自动推算（复利计算），其他项目仍可手工填入。
      </p>

      <div class="table-compact overflow-x-auto">
        <table class="data-table text-xs w-full">
          <thead>
            <tr>
              <th class="w-36 text-left sticky left-0 bg-stone-100 z-10">项目名称</th>
              <th v-for="m in months" :key="m" class="w-[64px] text-right whitespace-nowrap">{{ m }}</th>
              <th v-for="q in quarters" :key="q" class="w-[68px] text-right bg-amber-50 whitespace-nowrap">{{ q }}</th>
              <th class="w-[72px] text-right bg-stone-200 font-semibold whitespace-nowrap">年度合计</th>
              <th
                v-for="y in futureYears"
                :key="y"
                class="w-[80px] text-right bg-sky-100 font-semibold whitespace-nowrap"
              >
                {{ y }}规划
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in tableRows"
              :key="row.label"
              :class="{ 'font-semibold bg-stone-50': row.bold, 'bg-white': !row.bold }"
            >
              <td
                class="sticky left-0 z-10 font-medium"
                :class="{ 'pl-6': row.indent, 'bg-stone-50': row.bold, 'bg-white': !row.bold }"
              >
                {{ row.label }}
              </td>

              <!-- 12 monthly cells -->
              <td v-for="mi in 12" :key="'m' + row.label + mi" class="text-right p-0">
                <template v-if="row.type === 'manual'">
                  <input
                    type="number"
                    class="w-full text-right px-1 py-1 border border-transparent hover:border-stone-300 focus:border-amber-400 focus:outline-none bg-transparent font-number text-xs"
                    :value="row.getValue(mi - 1) != null ? row.getValue(mi - 1) : ''"
                    @input="
                      (e: Event) => {
                        const target = e.target as HTMLInputElement
                        const map: Record<string, (typeof manualKeys)[number]> = {
                          收入: 'revenue',
                          成本: 'cost',
                          经营费用: 'operatingExp',
                          管理费用: 'adminExp',
                          财务费用: 'financeExp',
                          营业外收支: 'otherIncExp',
                          所得税: 'incomeTax',
                        }
                        const key = map[row.label]
                        if (key) setValue(key, mi - 1, target.value)
                      }
                    "
                  />
                </template>
                <span v-else class="px-1 font-number text-stone-500">
                  {{ row.format ? row.format(row.getValue(mi - 1)) : '' }}
                </span>
              </td>

              <!-- Q1-Q4 subtotals -->
              <td
                v-for="q in 4"
                :key="'q' + row.label + q"
                class="text-right font-number bg-amber-50/30 text-stone-600 px-1"
              >
                {{
                  row.format
                    ? row.format(
                        qSum(
                          Array.from({ length: 12 }, (_, i) => getRowValues(row, i)),
                          q,
                        ),
                      )
                    : ''
                }}
              </td>

              <!-- Annual total -->
              <td class="text-right font-number font-semibold bg-stone-100 px-1 text-stone-700">
                {{ row.format ? row.format(annualSum(Array.from({ length: 12 }, (_, i) => row.getValue(i)))) : '' }}
              </td>

              <!-- Future year planning -->
              <td
                v-for="yi in 3"
                :key="'fy' + row.label + yi"
                class="text-right p-0"
                :class="yi === 1 ? 'bg-sky-50' : 'bg-sky-50/30'"
              >
                <!-- Revenue: auto-computed -->
                <template v-if="row.label === '收入'">
                  <span
                    class="px-1 font-number"
                    :class="getYearValue('收入', yi - 1) != null ? 'text-sky-700' : 'text-stone-300'"
                  >
                    {{ getYearValue('收入', yi - 1) != null ? fmt(getYearValue('收入', yi - 1)!) : '—' }}
                  </span>
                </template>
                <!-- Other manual rows -->
                <template v-else-if="row.type === 'manual'">
                  <input
                    type="number"
                    class="w-full text-right px-1 py-1 border border-transparent hover:border-sky-300 focus:border-sky-400 focus:outline-none bg-transparent font-number text-xs"
                    :value="getYearValue(row.label, yi - 1) != null ? getYearValue(row.label, yi - 1) : ''"
                    @input="
                      (e: Event) => {
                        const key = getYearInputKey(row.label)
                        if (key) setYearValue(key, yi - 1, (e.target as HTMLInputElement).value)
                      }
                    "
                  />
                </template>
                <!-- Auto rows (gross profit, net profit, etc.) -->
                <span v-else class="px-1 font-number text-stone-500">
                  {{ row.format ? row.format(getYearValue(row.label, yi - 1)) : '' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ═══════════ 预算完成情况分析 ═══════════ -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">预算完成情况分析</h3>
      <p class="text-[10px] text-stone-400 mb-2">收入、净利润实际数据从会计系统调用；完成率 = 实际 / 预算 × 100%。</p>

      <div class="table-compact overflow-x-auto">
        <table class="data-table text-xs w-full">
          <thead>
            <tr>
              <th class="w-32 text-left">项目</th>
              <th v-for="m in months" :key="'a' + m" class="w-[64px] text-right whitespace-nowrap">{{ m }} 实际</th>
              <th class="w-[72px] text-right bg-stone-200 whitespace-nowrap">年度实际</th>
              <th class="w-[72px] text-right bg-stone-200 whitespace-nowrap">年度预算</th>
              <th class="w-[72px] text-right bg-amber-50 whitespace-nowrap">完成率</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="font-medium">收入</td>
              <td v-for="mi in 12" :key="'ar' + mi" class="text-right font-number text-stone-500">
                {{ actualRevenue[mi - 1] != null ? actualRevenue[mi - 1]!.toLocaleString() : '—' }}
              </td>
              <td class="text-right font-number bg-stone-50 text-stone-500">
                {{ annualSum(actualRevenue) != null ? annualSum(actualRevenue)!.toLocaleString() : '—' }}
              </td>
              <td class="text-right font-number bg-stone-50">
                {{ fmt(annualSum(data.revenue)) }}
              </td>
              <td class="text-right font-number bg-amber-50/30">
                {{ revenueCompletion != null ? revenueCompletion.toFixed(1) + '%' : '—' }}
              </td>
            </tr>
            <tr>
              <td class="font-medium">净利润</td>
              <td v-for="mi in 12" :key="'np' + mi" class="text-right font-number text-stone-500">
                {{ actualNetProfit[mi - 1] != null ? actualNetProfit[mi - 1]!.toLocaleString() : '—' }}
              </td>
              <td class="text-right font-number bg-stone-50 text-stone-500">
                {{ annualSum(actualNetProfit) != null ? annualSum(actualNetProfit)!.toLocaleString() : '—' }}
              </td>
              <td class="text-right font-number bg-stone-50">
                {{ fmt(annualSum(netProfit)) }}
              </td>
              <td class="text-right font-number bg-amber-50/30">
                {{ profitCompletion != null ? profitCompletion.toFixed(1) + '%' : '—' }}
              </td>
            </tr>
            <tr class="bg-stone-50">
              <td class="font-medium pl-6">收入月度完成率</td>
              <td v-for="mi in 12" :key="'rc' + mi" class="text-right font-number text-stone-500">
                {{
                  data.revenue[mi - 1] != null && actualRevenue[mi - 1] != null && data.revenue[mi - 1] !== 0
                    ? ((actualRevenue[mi - 1]! / data.revenue[mi - 1]!) * 100).toFixed(1) + '%'
                    : '—'
                }}
              </td>
              <td class="text-right font-number bg-stone-50 text-stone-500" colspan="2">—</td>
              <td class="text-right font-number bg-amber-50/30">
                {{ revenueCompletion != null ? revenueCompletion.toFixed(1) + '%' : '—' }}
              </td>
            </tr>
            <tr class="bg-stone-50">
              <td class="font-medium pl-6">净利润月度完成率</td>
              <td v-for="mi in 12" :key="'nc' + mi" class="text-right font-number text-stone-500">
                {{
                  netProfit[mi - 1] != null && actualNetProfit[mi - 1] != null && netProfit[mi - 1] !== 0
                    ? ((actualNetProfit[mi - 1]! / netProfit[mi - 1]!) * 100).toFixed(1) + '%'
                    : '—'
                }}
              </td>
              <td class="text-right font-number bg-stone-50 text-stone-500" colspan="2">—</td>
              <td class="text-right font-number bg-amber-50/30">
                {{ profitCompletion != null ? profitCompletion.toFixed(1) + '%' : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
