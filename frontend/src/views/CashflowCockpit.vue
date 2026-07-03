<script setup lang="ts">
import { reactive, computed } from 'vue'

const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

// ── Manual input data (12 months each) ──
const data = reactive({
  openingBalance: Array(12).fill(null) as (number | null)[], // 期初余额
  salesCollection: Array(12).fill(null) as (number | null)[], // 销售回款
  investmentDiv: Array(12).fill(null) as (number | null)[], // 投资变现与分红
  otherInflow: Array(12).fill(null) as (number | null)[], // 其他流入
  purchaseCost: Array(12).fill(null) as (number | null)[], // 采购成本
  marketingExp: Array(12).fill(null) as (number | null)[], // 营销费用
  rdExp: Array(12).fill(null) as (number | null)[], // 研发费用
  adminExp: Array(12).fill(null) as (number | null)[], // 管理费用
  financeExp: Array(12).fill(null) as (number | null)[], // 财务费用
  equityInv: Array(12).fill(null) as (number | null)[], // 投资-股权
  officeInv: Array(12).fill(null) as (number | null)[], // 投资-办公楼
  landInv: Array(12).fill(null) as (number | null)[], // 投资-土地
  constructionInv: Array(12).fill(null) as (number | null)[], // 投资-建安
  otherOutflow: Array(12).fill(null) as (number | null)[], // 其他流出
  // 融资计划
  equityFin: Array(12).fill(null) as (number | null)[], // 股权融资
  debtFin: Array(12).fill(null) as (number | null)[], // 债务融资
})

const manualKeys = [
  'openingBalance',
  'salesCollection',
  'investmentDiv',
  'otherInflow',
  'purchaseCost',
  'marketingExp',
  'rdExp',
  'adminExp',
  'financeExp',
  'equityInv',
  'officeInv',
  'landInv',
  'constructionInv',
  'otherOutflow',
  'equityFin',
  'debtFin',
] as const
type ManualKey = (typeof manualKeys)[number]

function setValue(key: ManualKey, mi: number, val: string) {
  const n = parseFloat(val)
  ;(data[key] as (number | null)[])[mi] = isNaN(n) ? null : n
}

// Future year annual planning (2027-2029)
const yearData = reactive<Record<ManualKey, (number | null)[]>>({
  openingBalance: [null, null, null],
  salesCollection: [null, null, null],
  investmentDiv: [null, null, null],
  otherInflow: [null, null, null],
  purchaseCost: [null, null, null],
  marketingExp: [null, null, null],
  rdExp: [null, null, null],
  adminExp: [null, null, null],
  financeExp: [null, null, null],
  equityInv: [null, null, null],
  officeInv: [null, null, null],
  landInv: [null, null, null],
  constructionInv: [null, null, null],
  otherOutflow: [null, null, null],
  equityFin: [null, null, null],
  debtFin: [null, null, null],
})
const currentYear = new Date().getFullYear()
const futureYears = [`${currentYear + 1}年`, `${currentYear + 2}年`, `${currentYear + 3}年`]

function setYearValue(key: ManualKey, yi: number, val: string) {
  const n = parseFloat(val)
  yearData[key][yi] = isNaN(n) ? null : n
}

// ── Auto-computed values ──
const investmentTotal = computed(() =>
  data.equityInv.map((_, i) => {
    const vals = [data.equityInv[i], data.officeInv[i], data.landInv[i], data.constructionInv[i]]
    if (vals.every(v => v == null)) return null
    return vals.reduce((a: number, v) => a + (v ?? 0), 0)
  }),
)
const inflowTotal = computed(() =>
  data.salesCollection.map((_, i) => {
    const vals = [data.salesCollection[i], data.investmentDiv[i], data.otherInflow[i]]
    if (vals.every(v => v == null)) return null
    return vals.reduce((a: number, v) => a + (v ?? 0), 0)
  }),
)
const outflowTotal = computed(() =>
  data.purchaseCost.map((_, i) => {
    const vals = [
      data.purchaseCost[i],
      data.marketingExp[i],
      data.rdExp[i],
      data.adminExp[i],
      data.financeExp[i],
      investmentTotal.value[i],
      data.otherOutflow[i],
    ]
    if (vals.every(v => v == null)) return null
    return vals.reduce((a: number, v) => a + (v ?? 0), 0)
  }),
)
// Rolling balance: 1月期初=手动, 2-12月期初=上月资金余额
const rollingBalance = computed(() => {
  const result: (number | null)[] = []
  for (let i = 0; i < 12; i++) {
    const ob = i === 0 ? data.openingBalance[0] : result[i - 1]
    const inflow = inflowTotal.value[i]
    const outflow = outflowTotal.value[i]
    if (ob == null && inflow == null && outflow == null) {
      result[i] = null
    } else {
      result[i] = (ob ?? 0) + (inflow ?? 0) - (outflow ?? 0)
    }
  }
  return result
})

const effectiveOpening = computed(() => {
  const result: (number | null)[] = [data.openingBalance[0]]
  for (let i = 1; i < 12; i++) result[i] = rollingBalance.value[i - 1]
  return result
})
const financingTotal = computed(() =>
  data.equityFin.map((_, i) => {
    const e = data.equityFin[i]
    const d = data.debtFin[i]
    if (e == null && d == null) return null
    return (e ?? 0) + (d ?? 0)
  }),
)

// ── Helpers ──
function annualSum(values: (number | null)[]): number | null {
  if (values.every(v => v == null)) return null
  return values.reduce((a: number, v) => a + (v ?? 0), 0)
}
function qSum(values: (number | null)[], q: number): number | null {
  const start = (q - 1) * 3
  const slice = values.slice(start, start + 3)
  if (slice.every(v => v == null)) return null
  return slice.reduce((a: number, v) => a + (v ?? 0), 0)
}
const quarters = ['Q1小计', 'Q2小计', 'Q3小计', 'Q4小计']
function fmt(v: number | null): string {
  if (v == null) return ''
  return v.toLocaleString()
}

// ── Cashflow table row definitions ──
interface TableRow {
  seq: string
  item: string
  type: 'header' | 'manual' | 'auto' | 'summary'
  indent?: boolean
  bold?: boolean
  getValue: (mi: number) => number | null
  bgClass?: string
  inputKey?: ManualKey
}

const cashflowRows = computed<TableRow[]>(() => [
  {
    seq: '—',
    item: '期初余额',
    type: 'manual',
    bold: true,
    bgClass: 'bg-stone-50',
    getValue: i => effectiveOpening.value[i],
    inputKey: 'openingBalance',
  },
  { seq: '一', item: '资金流入', type: 'header', bgClass: 'bg-emerald-50', getValue: () => null },
  {
    seq: '1',
    item: '销售回款',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.salesCollection[i],
    inputKey: 'salesCollection',
  },
  {
    seq: '2',
    item: '投资变现与分红',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.investmentDiv[i],
    inputKey: 'investmentDiv',
  },
  {
    seq: '3',
    item: '其他',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.otherInflow[i],
    inputKey: 'otherInflow',
  },
  {
    seq: '',
    item: '实际回款合计',
    type: 'auto',
    bold: true,
    bgClass: 'bg-emerald-50',
    getValue: i => inflowTotal.value[i],
  },
  { seq: '二', item: '资金流出', type: 'header', bgClass: 'bg-red-50', getValue: () => null },
  {
    seq: '4',
    item: '采购成本',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.purchaseCost[i],
    inputKey: 'purchaseCost',
  },
  {
    seq: '5',
    item: '营销费用',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.marketingExp[i],
    inputKey: 'marketingExp',
  },
  {
    seq: '6',
    item: '研发费用',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.rdExp[i],
    inputKey: 'rdExp',
  },
  {
    seq: '7',
    item: '管理费用',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.adminExp[i],
    inputKey: 'adminExp',
  },
  {
    seq: '8',
    item: '财务费用',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.financeExp[i],
    inputKey: 'financeExp',
  },
  {
    seq: '9',
    item: '投资',
    type: 'auto',
    indent: true,
    bold: true,
    bgClass: 'bg-stone-50',
    getValue: i => investmentTotal.value[i],
  },
  {
    seq: '',
    item: '股权',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.equityInv[i],
    inputKey: 'equityInv',
  },
  {
    seq: '',
    item: '办公楼',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.officeInv[i],
    inputKey: 'officeInv',
  },
  {
    seq: '',
    item: '土地',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.landInv[i],
    inputKey: 'landInv',
  },
  {
    seq: '',
    item: '建安',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.constructionInv[i],
    inputKey: 'constructionInv',
  },
  {
    seq: '10',
    item: '其他',
    type: 'manual',
    indent: true,
    bgClass: 'bg-white',
    getValue: i => data.otherOutflow[i],
    inputKey: 'otherOutflow',
  },
  {
    seq: '',
    item: '实际支付合计',
    type: 'auto',
    bold: true,
    bgClass: 'bg-red-50',
    getValue: i => outflowTotal.value[i],
  },
  { seq: '', item: '资金余额', type: 'auto', bold: true, bgClass: 'bg-sky-50', getValue: i => rollingBalance.value[i] },
])

// ── Financing table rows ──
const financingRows = computed<TableRow[]>(() => [
  {
    seq: '—',
    item: '股权融资',
    type: 'manual',
    bold: true,
    bgClass: 'bg-white',
    getValue: i => data.equityFin[i],
    inputKey: 'equityFin',
  },
  {
    seq: '—',
    item: '债务融资',
    type: 'manual',
    bold: true,
    bgClass: 'bg-white',
    getValue: i => data.debtFin[i],
    inputKey: 'debtFin',
  },
  {
    seq: '',
    item: '融资合计',
    type: 'auto',
    bold: true,
    bgClass: 'bg-stone-50',
    getValue: i => financingTotal.value[i],
  },
])
</script>

<template>
  <div class="space-y-6">
    <div class="page-header">
      <h2>现金流计划与融资计划</h2>
    </div>

    <!-- ═══════════ 现金流计划表 ═══════════ -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">现金流计划表</h3>
      <p class="text-[10px] text-stone-400 mb-2">
        月度数据手工填入；实际回款合计 = 销售回款 + 投资变现与分红 + 其他； 投资 = 股权 + 办公楼 + 土地 +
        建安；实际支付合计 = 采购成本 + 营销 + 研发 + 管理 + 财务 + 投资 + 其他； 资金余额 = 期初余额 + 实际回款 −
        实际支付。
      </p>

      <div class="table-compact overflow-x-auto">
        <table class="data-table text-xs w-full">
          <thead>
            <tr>
              <th class="w-8 text-center">序号</th>
              <th class="w-36 text-left">项目</th>
              <th v-for="m in months" :key="m" class="w-[64px] text-right">{{ m }}</th>
              <th v-for="q in quarters" :key="q" class="w-[68px] text-right bg-amber-50">{{ q }}</th>
              <th class="w-[72px] text-right bg-stone-200 font-semibold">年度合计</th>
              <th v-for="y in futureYears" :key="'cf' + y" class="w-[72px] text-right bg-sky-100 font-semibold">
                {{ y }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in cashflowRows"
              :key="row.item + row.seq"
              :class="[
                row.bgClass,
                { 'font-semibold': row.bold || row.type === 'header' },
                { 'text-emerald-700': row.type === 'header' && row.seq === '一' },
                { 'text-red-700': row.type === 'header' && row.seq === '二' },
              ]"
            >
              <!-- 序号 -->
              <td class="text-center text-stone-400 text-[10px]">{{ row.seq }}</td>

              <!-- 项目名称 -->
              <td
                :class="{
                  'pl-6': row.indent,
                  'font-medium': !row.indent && row.type !== 'header',
                  'text-emerald-700': row.seq === '一',
                  'text-red-700': row.seq === '二',
                }"
              >
                {{ row.item }}
              </td>

              <!-- Monthly cells -->
              <td v-for="mi in 12" :key="'m' + row.item + mi" class="text-right p-0">
                <!-- 期初余额: only January (mi=1) is manual; Feb-Dec = auto from previous month balance -->
                <template v-if="row.type === 'manual' && row.inputKey && !(row.item === '期初余额' && mi > 1)">
                  <input
                    type="number"
                    class="w-full text-right px-1 py-1 border border-transparent hover:border-stone-300 focus:border-amber-400 focus:outline-none bg-transparent font-number text-xs"
                    :value="row.getValue(mi - 1) != null ? row.getValue(mi - 1) : ''"
                    @input="
                      (e: Event) => {
                        if (row.inputKey) setValue(row.inputKey, mi - 1, (e.target as HTMLInputElement).value)
                      }
                    "
                  />
                </template>
                <template v-else-if="row.type === 'header'"></template>
                <span v-else class="px-1 font-number text-stone-500">
                  {{ fmt(row.getValue(mi - 1)) }}
                </span>
              </td>

              <!-- Quarterly cells (auto) -->
              <td
                v-for="q in 4"
                :key="'qc' + row.item + q"
                class="text-right font-number bg-amber-50/30 text-stone-600 px-1"
              >
                <template v-if="row.type === 'header'"></template>
                <span v-else>{{
                  fmt(
                    qSum(
                      Array.from({ length: 12 }, (_, i) => row.getValue(i)),
                      q,
                    ),
                  )
                }}</span>
              </td>

              <!-- Annual total -->
              <td
                class="text-right font-number font-semibold bg-stone-100 px-1"
                :class="{
                  'text-stone-700': row.type === 'auto' || row.type === 'summary',
                  'text-stone-400': row.type === 'manual',
                }"
              >
                {{ row.type !== 'header' ? fmt(annualSum(Array.from({ length: 12 }, (_, i) => row.getValue(i)))) : '' }}
              </td>

              <!-- Future year cells (2027-2029) -->
              <td
                v-for="yi in 3"
                :key="'cfy' + row.item + yi"
                class="text-right p-0"
                :class="yi === 0 ? 'bg-sky-50' : 'bg-sky-50/30'"
              >
                <template v-if="row.type !== 'header' && row.inputKey">
                  <input
                    type="number"
                    class="w-full text-right px-1 py-1 border border-transparent hover:border-sky-300 focus:border-sky-400 focus:outline-none bg-transparent font-number text-xs"
                    :value="row.inputKey ? (yearData[row.inputKey][yi] != null ? yearData[row.inputKey][yi] : '') : ''"
                    @input="
                      (e: Event) => {
                        if (row.inputKey) setYearValue(row.inputKey, yi, (e.target as HTMLInputElement).value)
                      }
                    "
                  />
                </template>
                <span v-else-if="row.type !== 'header'" class="px-1 font-number text-stone-500">
                  {{ fmt(row.inputKey ? yearData[row.inputKey][yi] : null) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ═══════════ 融资计划总表 ═══════════ -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">融资计划总表</h3>
      <p class="text-[10px] text-stone-400 mb-2">股权融资、债务融资月度数据手工填入；融资合计自动计算。</p>

      <div class="table-compact overflow-x-auto">
        <table class="data-table text-xs w-full">
          <thead>
            <tr>
              <th class="w-8 text-center">序号</th>
              <th class="w-36 text-left">项目</th>
              <th v-for="m in months" :key="'fm' + m" class="w-[64px] text-right">{{ m }}</th>
              <th v-for="q in quarters" :key="'fq' + q" class="w-[68px] text-right bg-amber-50">{{ q }}</th>
              <th class="w-[72px] text-right bg-stone-200 font-semibold">年度合计</th>
              <th v-for="y in futureYears" :key="'ff' + y" class="w-[72px] text-right bg-sky-100 font-semibold">
                {{ y }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in financingRows" :key="row.item" :class="[row.bgClass, { 'font-semibold': row.bold }]">
              <td class="text-center text-stone-400 text-[10px]">{{ row.seq }}</td>
              <td class="font-medium">{{ row.item }}</td>

              <td v-for="mi in 12" :key="'fm' + row.item + mi" class="text-right p-0">
                <template v-if="row.type === 'manual' && row.inputKey">
                  <input
                    type="number"
                    class="w-full text-right px-1 py-1 border border-transparent hover:border-stone-300 focus:border-amber-400 focus:outline-none bg-transparent font-number text-xs"
                    :value="row.getValue(mi - 1) != null ? row.getValue(mi - 1) : ''"
                    @input="(e: Event) => setValue(row.inputKey!, mi - 1, (e.target as HTMLInputElement).value)"
                  />
                </template>
                <span v-else class="px-1 font-number text-stone-500">
                  {{ fmt(row.getValue(mi - 1)) }}
                </span>
              </td>

              <!-- Quarterly cells (auto) -->
              <td
                v-for="q in 4"
                :key="'fq' + row.item + q"
                class="text-right font-number bg-amber-50/30 text-stone-600 px-1"
              >
                {{
                  fmt(
                    qSum(
                      Array.from({ length: 12 }, (_, i) => row.getValue(i)),
                      q,
                    ),
                  )
                }}
              </td>

              <td
                class="text-right font-number font-semibold bg-stone-100 px-1"
                :class="{ 'text-stone-700': row.type === 'auto', 'text-stone-400': row.type === 'manual' }"
              >
                {{ fmt(annualSum(Array.from({ length: 12 }, (_, i) => row.getValue(i)))) }}
              </td>

              <!-- Future year cells -->
              <td
                v-for="yi in 3"
                :key="'ffy' + row.item + yi"
                class="text-right p-0"
                :class="yi === 0 ? 'bg-sky-50' : 'bg-sky-50/30'"
              >
                <template v-if="row.inputKey">
                  <input
                    type="number"
                    class="w-full text-right px-1 py-1 border border-transparent hover:border-sky-300 focus:border-sky-400 focus:outline-none bg-transparent font-number text-xs"
                    :value="yearData[row.inputKey][yi] != null ? yearData[row.inputKey][yi] : ''"
                    @input="(e: Event) => setYearValue(row.inputKey!, yi, (e.target as HTMLInputElement).value)"
                  />
                </template>
                <span v-else class="px-1 font-number text-stone-500">
                  {{ fmt(null) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ═══════════ 一、债务融资明细 ═══════════ -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">一、债务融资</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <!-- 1.1 时间 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">1.1 计划融资时间</label>
          <input
            type="date"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none"
          />
        </div>
        <!-- 1.2 规模 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">1.2 计划融资规模（万元）</label>
          <input
            type="number"
            placeholder="输入金额"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none font-number"
          />
        </div>
        <!-- 1.3 财务费用 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide"
            >1.3 财务费用水平（年化利率 %）</label
          >
          <input
            type="number"
            step="0.01"
            placeholder="例如：4.35"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none font-number"
          />
        </div>
        <!-- 1.4 金融机构 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">1.4 金融机构名称</label>
          <input
            type="text"
            placeholder="例如：XX银行"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none"
          />
        </div>
      </div>
    </div>

    <!-- ═══════════ 二、股权融资明细 ═══════════ -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">二、股权融资</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <!-- 2.1 时间 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">2.1 计划融资时间</label>
          <input
            type="date"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none"
          />
        </div>
        <!-- 2.2 规模 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">2.2 计划融资规模（万元）</label>
          <input
            type="number"
            placeholder="输入金额"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none font-number"
          />
        </div>
        <!-- 2.3 保荐人/投行 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white md:col-span-2">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">2.3 保荐人/投行顾问</label>
          <div class="flex gap-2">
            <input
              type="text"
              placeholder="机构名称"
              class="flex-1 text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none"
            />
            <div class="flex items-center gap-1 bg-stone-50 rounded-sm px-2 border border-stone-200">
              <span class="text-[10px] text-stone-400 whitespace-nowrap">费率 %</span>
              <input
                type="number"
                step="0.01"
                placeholder="—"
                class="w-16 text-xs px-1 py-1.5 bg-transparent focus:outline-none font-number text-right"
              />
            </div>
          </div>
        </div>
        <!-- 2.4 律所 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white md:col-span-2">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">2.4 律师事务所</label>
          <div class="flex gap-2">
            <input
              type="text"
              placeholder="律所名称"
              class="flex-1 text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none"
            />
            <div class="flex items-center gap-1 bg-stone-50 rounded-sm px-2 border border-stone-200">
              <span class="text-[10px] text-stone-400 whitespace-nowrap">费用 万元</span>
              <input
                type="number"
                placeholder="—"
                class="w-16 text-xs px-1 py-1.5 bg-transparent focus:outline-none font-number text-right"
              />
            </div>
          </div>
        </div>
        <!-- 2.5 会所 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white md:col-span-2">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">2.5 会计师事务所</label>
          <div class="flex gap-2">
            <input
              type="text"
              placeholder="会所名称"
              class="flex-1 text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none"
            />
            <div class="flex items-center gap-1 bg-stone-50 rounded-sm px-2 border border-stone-200">
              <span class="text-[10px] text-stone-400 whitespace-nowrap">费用 万元</span>
              <input
                type="number"
                placeholder="—"
                class="w-16 text-xs px-1 py-1.5 bg-transparent focus:outline-none font-number text-right"
              />
            </div>
          </div>
        </div>
        <!-- 2.6 估值 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">2.6 公司估值预期（万元）</label>
          <input
            type="number"
            placeholder="投前/投后估值"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none font-number"
          />
        </div>
        <!-- 2.7 股份比例 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">2.7 股份比例对价（%）</label>
          <input
            type="number"
            step="0.01"
            placeholder="稀释比例"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none font-number"
          />
        </div>
        <!-- 2.8 融资轮次 -->
        <div class="border border-stone-200 rounded-sm p-3 bg-white">
          <label class="text-[10px] text-stone-400 mb-1 block uppercase tracking-wide">2.8 融资轮次</label>
          <input
            type="text"
            placeholder="天使轮 / A轮 / B轮 / Pre-IPO"
            class="w-full text-xs px-2 py-1.5 border border-stone-200 rounded-sm focus:border-amber-400 focus:outline-none"
          />
        </div>
      </div>
    </div>
  </div>
</template>
