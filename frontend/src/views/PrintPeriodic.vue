<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import { printPeriodic } from '@/api'

const route = useRoute()
const data = ref<any>(null)
const loading = ref(false)
const currentPeriod = ref(new Date().toISOString().slice(0, 7))
const selectedReport = ref('balance')
const selectedYear = ref(new Date().getFullYear())
const selectedQuarter = ref(Math.ceil((new Date().getMonth() + 1) / 3))

const REPORT_OPTIONS = [
  { label: '资产负债表', value: 'balance' },
  { label: '利润表', value: 'income' },
  { label: '现金流量表', value: 'cashflow' },
]

const QUARTER_OPTIONS = [
  { label: '第一季度 (1-3月)', value: 1 },
  { label: '第二季度 (4-6月)', value: 2 },
  { label: '第三季度 (7-9月)', value: 3 },
  { label: '第四季度 (10-12月)', value: 4 },
]

const reportType = computed(() => {
  const path = route.path
  if (path.includes('quarterly')) return 'quarterly'
  if (path.includes('yearly')) return 'yearly'
  return 'monthly'
})

const isPrintView = computed(() => route.path.startsWith('/print'))
const pageTitle = computed(() => {
  const t = reportType.value
  const suffix = isPrintView.value ? '打印' : ''
  return t === 'quarterly' ? `季度报表${suffix}` : t === 'yearly' ? `年度报表${suffix}` : `月度报表${suffix}`
})

// Build the effective period string based on type
const effectivePeriod = computed(() => {
  if (reportType.value === 'yearly') return `${selectedYear.value}-12`
  if (reportType.value === 'quarterly') {
    const lastMonth = selectedQuarter.value * 3
    return `${selectedYear.value}-${String(lastMonth).padStart(2, '0')}`
  }
  return currentPeriod.value
})

watch(selectedReport, load)
watch(effectivePeriod, load)

function formatNumber(val: number | null) {
  if (val === null || val === undefined) return ''
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await printPeriodic(cid, effectivePeriod.value, selectedReport.value, reportType.value)
    data.value = res.data
  } catch (e: any) {
    alert(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function doPrint() { window.print() }

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center flex-wrap">
        <!-- Year selector (for quarterly & yearly) -->
        <template v-if="reportType !== 'monthly'">
          <input v-model="selectedYear" type="number" :min="2020" :max="2099" class="px-3 py-2 border border-zinc-300 rounded-sm text-sm w-24" />
        </template>
        <!-- Quarter selector (for quarterly) -->
        <Dropdown v-if="reportType === 'quarterly'" v-model="selectedQuarter" :options="QUARTER_OPTIONS" optionLabel="label" optionValue="value" class="w-48" />
        <!-- Month selector (for monthly) -->
        <input v-if="reportType === 'monthly'" v-model="currentPeriod" type="month" class="px-3 py-2 border border-zinc-300 rounded-sm text-sm" />
        <Dropdown v-model="selectedReport" :options="REPORT_OPTIONS" optionLabel="label" optionValue="value" class="w-40" />
        <Button label="打印" icon="pi pi-print" @click="doPrint" :disabled="!data" />
      </div>
    </div>

    <p v-if="loading" class="text-zinc-400 text-sm">加载中...</p>

    <!-- 资产负债表 -->
    <div v-if="selectedReport === 'balance' && data" class="print-area bg-white shadow-sm px-12 pt-8 pb-4 max-w-[96%] mx-auto">
      <h1 class="text-2xl font-bold text-center mb-4">资产负债表</h1>
      <div class="flex justify-between text-sm text-gray-600 mb-4">
        <span>{{ data.date_display }}</span>
        <span>金额单位：元</span>
      </div>
      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400">
            <th class="text-left py-1.5 px-2 font-bold bg-stone-50 border border-stone-200" style="width:30%">资 产</th>
            <th class="text-right py-1.5 px-2 font-bold bg-stone-50 border border-stone-200 report-number" style="width:12%">期末余额</th>
            <th class="text-right py-1.5 px-2 font-bold bg-stone-50 border border-stone-200 report-number" style="width:12%">年初余额</th>
            <th class="text-left py-1.5 px-2 font-bold bg-stone-50 border border-stone-200" style="width:30%">负债及所有者权益</th>
            <th class="text-right py-1.5 px-2 font-bold bg-stone-50 border border-stone-200 report-number" style="width:12%">期末余额</th>
            <th class="text-right py-1.5 px-2 font-bold bg-stone-50 border border-stone-200 report-number" style="width:12%">年初余额</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in Math.max(data.left_items?.length || 0, data.right_items?.length || 0)" :key="i">
            <td v-if="data.left_items?.[i-1]" class="py-1.5 px-2 border border-stone-200"
                :class="{ 'font-bold bg-stone-50': data.left_items[i-1].name.includes('合计') || data.left_items[i-1].name.includes('总计') }">
              {{ data.left_items[i-1].name }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td v-if="data.left_items?.[i-1]" class="report-number py-1.5 px-2 border border-stone-200"
                :class="{ 'font-bold bg-stone-50': data.left_items[i-1].name.includes('合计') || data.left_items[i-1].name.includes('总计') }">
              {{ formatNumber(data.left_items[i-1].ending) }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td v-if="data.left_items?.[i-1]" class="report-number py-1.5 px-2 border border-stone-200"
                :class="{ 'font-bold bg-stone-50': data.left_items[i-1].name.includes('合计') || data.left_items[i-1].name.includes('总计') }">
              {{ formatNumber(data.left_items[i-1].beginning) }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td v-if="data.right_items?.[i-1]" class="py-1.5 px-2 border border-stone-200"
                :class="{ 'font-bold bg-stone-50': data.right_items[i-1].name.includes('合计') || data.right_items[i-1].name.includes('总计') }">
              {{ data.right_items[i-1].name }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td v-if="data.right_items?.[i-1]" class="report-number py-1.5 px-2 border border-stone-200"
                :class="{ 'font-bold bg-stone-50': data.right_items[i-1].name.includes('合计') || data.right_items[i-1].name.includes('总计') }">
              {{ formatNumber(data.right_items[i-1].ending) }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td v-if="data.right_items?.[i-1]" class="report-number py-1.5 px-2 border border-stone-200"
                :class="{ 'font-bold bg-stone-50': data.right_items[i-1].name.includes('合计') || data.right_items[i-1].name.includes('总计') }">
              {{ formatNumber(data.right_items[i-1].beginning) }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
          </tr>
        </tbody>
      </table>
      <div class="flex justify-between text-sm text-gray-600 mt-6 pt-3 border-t border-gray-300">
        <span>公司负责人：</span>
        <span>财务负责人：</span>
        <span>制表人：&emsp;&emsp;&emsp;</span>
      </div>
    </div>

    <!-- 利润表 -->
    <div v-if="selectedReport === 'income' && data" class="print-area bg-white shadow-sm px-12 pt-8 pb-4 max-w-5xl mx-auto">
      <h1 class="text-2xl font-bold text-center mb-4">利润表</h1>
      <div class="flex justify-between text-sm text-gray-600 mb-4">
        <span>{{ data.period_display }}</span>
        <span>金额单位：元</span>
      </div>
      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400 bg-stone-50">
            <th class="text-left py-1.5 px-2 border border-stone-200" style="width:50%">项 目</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number" style="width:17%">本期金额</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number" style="width:17%">本年累计</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number" style="width:17%">上年同期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in data.items" :key="item.name">
            <td class="py-1.5 px-2 border border-stone-200"
                :class="{ 'font-bold bg-stone-50': item.name.includes('营业利润') || item.name.includes('利润总额') || item.name.includes('净利润') }">
              {{ item.name }}
            </td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(item.curr) }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(item.ytd) }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(item.prev) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="flex justify-between text-sm text-gray-600 mt-6 pt-3 border-t border-gray-300">
        <span>公司负责人：</span>
        <span>财务负责人：</span>
        <span>制表人：&emsp;&emsp;&emsp;</span>
      </div>
    </div>

    <!-- 现金流量表 -->
    <div v-if="selectedReport === 'cashflow' && data" class="print-area bg-white shadow-sm px-12 pt-8 pb-4 max-w-5xl mx-auto">
      <h1 class="text-2xl font-bold text-center mb-4">现金流量表</h1>
      <div class="flex justify-between text-sm text-gray-600 mb-4">
        <span>{{ data.date_display }}</span>
        <span>金额单位：元</span>
      </div>
      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400 bg-stone-50">
            <th class="text-left py-1.5 px-2 border border-stone-200" style="width:50%">项 目</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number" style="width:17%">金额</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number" style="width:17%">累计</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number" style="width:17%">同期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in data.rows" :key="idx">
            <td class="py-1.5 px-2 border border-stone-200">{{ row[0] }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(row[1]) }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(row[2]) }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(row[3]) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="flex justify-between text-sm text-gray-600 mt-6 pt-3 border-t border-gray-300">
        <span>公司负责人：</span>
        <span>财务负责人：</span>
        <span>制表人：&emsp;&emsp;&emsp;</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media print {
  @page { size: A4 portrait; margin: 10mm; }
  body * { visibility: hidden; }
  .print-area, .print-area * { visibility: visible; }
  .print-area { position: absolute; left: 0; top: 0; width: 100%; margin: 0 auto; }
}
</style>
