<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import { listPeriods, printPeriodic, exportPeriodicExcel } from '@/api'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const route = useRoute()
const data = ref<any>(null)
const loading = ref(false)
const selectedReport = ref('balance')
const allClosedPeriods = ref<string[]>([])
const selectedPeriod = ref<string>('')
const noDataMessage = ref('')

const REPORT_OPTIONS = computed(() => [
  { label: t('accounting.prints_page.balanceSheet'), value: 'balance' },
  { label: t('accounting.prints_page.incomeStatement'), value: 'income' },
  { label: t('accounting.prints_page.cashflowStatement'), value: 'cashflow' },
])

const reportType = computed(() => {
  const path = route.path
  if (path.includes('quarterly')) return 'quarterly'
  if (path.includes('yearly')) return 'yearly'
  return 'monthly'
})

const isPrintView = computed(() => route.path.startsWith('/print'))
const _pageTitle = computed(() => {
  const t = reportType.value
  const suffix = isPrintView.value ? '打印' : ''
  return t === 'quarterly' ? `季度报表${suffix}` : t === 'yearly' ? `年度报表${suffix}` : `月度报表${suffix}`
})

// ── 按类型筛选可用期间 ──
interface PeriodOption {
  label: string
  value: string
  isClosed?: boolean
}

const currentYear = new Date().getFullYear()
const currentMonth = `${currentYear}-${String(new Date().getMonth() + 1).padStart(2, '0')}`

const periodOptions = computed<PeriodOption[]>(() => {
  if (reportType.value === 'monthly') {
    // 月度：显示全部 12 个月，标记是否已关帐
    const months: PeriodOption[] = []
    for (let m = 1; m <= 12; m++) {
      const period = `${currentYear}-${String(m).padStart(2, '0')}`
      const isClosed = allClosedPeriods.value.includes(period)
      months.push({ label: `${currentYear} 年 ${String(m).padStart(2, '0')} 月`, value: period, isClosed })
    }
    return months
  }
  if (reportType.value === 'quarterly') {
    const quarters: PeriodOption[] = []
    for (const [qi, months] of [
      [1, ['01', '02', '03']],
      [2, ['04', '05', '06']],
      [3, ['07', '08', '09']],
      [4, ['10', '11', '12']],
    ] as [number, string[]][]) {
      const allClosed = months.every(m => allClosedPeriods.value.includes(`${currentYear}-${m}`))
      const lastMonth = String(qi * 3).padStart(2, '0')
      quarters.push({ label: `${currentYear} 年第${qi}季度`, value: `${currentYear}-${lastMonth}`, isClosed: allClosed })
    }
    return quarters
  }
  // yearly：显示本年度，标记是否 12 个月全部关帐
  const yearClosed = Array.from({ length: 12 }, (_, i) => `${currentYear}-${String(i + 1).padStart(2, '0')}`)
    .every(m => allClosedPeriods.value.includes(m))
  return [{ label: `${currentYear} 年度`, value: `${currentYear}-12`, isClosed: yearClosed }]
})

const currentQuarter = Math.ceil((new Date().getMonth() + 1) / 3)
const currentQuarterPeriod = `${currentYear}-${String(currentQuarter * 3).padStart(2, '0')}`

// 默认选当前月份/季度/年度；切换类型时重置
watch(reportType, () => {
  if (reportType.value === 'monthly') {
    selectedPeriod.value = currentMonth
  } else if (reportType.value === 'quarterly') {
    selectedPeriod.value = currentQuarterPeriod
  } else if (reportType.value === 'yearly') {
    selectedPeriod.value = `${currentYear}-12`
  } else {
    selectedPeriod.value = ''
  }
  noDataMessage.value = ''
})

watch(selectedReport, loadReport)
watch(selectedPeriod, loadReport)

function formatNumber(val: number | null) {
  if (val === null || val === undefined) return ''
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function fetchClosedPeriods() {
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await listPeriods(cid)
    allClosedPeriods.value = (res.data || [])
      .filter((p: any) => p.is_closed)
      .map((p: any) => p.period)
      .sort()
    // 默认选中当前月份/季度/年度
    if (reportType.value === 'quarterly') {
      selectedPeriod.value = currentQuarterPeriod
    } else if (reportType.value === 'yearly') {
      selectedPeriod.value = `${currentYear}-12`
    } else {
      selectedPeriod.value = currentMonth
    }
    noDataMessage.value = ''
  } catch {
    noDataMessage.value = '加载期间数据失败'
  }
}

async function loadReport() {
  if (!selectedPeriod.value) {
    data.value = null
    return
  }
  // 未关帐月份：显示提示，不加载数据
  const option = periodOptions.value.find(o => o.value === selectedPeriod.value)
  if (option && !option.isClosed) {
    data.value = null
    noDataMessage.value = `期间 ${selectedPeriod.value} 尚未关帐，请先完成月度结账后再查看报表。`
    return
  }
  noDataMessage.value = ''
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await printPeriodic(cid, selectedPeriod.value, selectedReport.value, reportType.value)
    data.value = res.data
  } catch (e: any) {
    alert(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const exporting = ref(false)

async function doExport() {
  if (!selectedPeriod.value) return
  exporting.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    await exportPeriodicExcel(cid, selectedPeriod.value, selectedReport.value, reportType.value)
  } catch (e: any) {
    alert('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    exporting.value = false
  }
}

function doPrint() {
  window.print()
}

onMounted(fetchClosedPeriods)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center flex-wrap">
        <Dropdown
          v-model="selectedPeriod"
          :options="periodOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="noDataMessage || '请选择期间'"
          class="w-52"
          :disabled="periodOptions.length === 0"
        />
        <Dropdown
          v-model="selectedReport"
          :options="REPORT_OPTIONS"
          optionLabel="label"
          optionValue="value"
          class="w-40"
        />
        <Button :label="t('accounting.prints_page.exportExcel')" icon="pi pi-file-excel" severity="success" @click="doExport" :disabled="!data" :loading="exporting" />
        <Button :label="t('accounting.prints_page.printPDF')" icon="pi pi-print" @click="doPrint" :disabled="!data" />
      </div>
      <p v-if="noDataMessage && periodOptions.length === 0" class="text-zinc-400 text-sm mt-2">{{ noDataMessage }}</p>
    </div>

    <p v-if="loading" class="text-zinc-400 text-sm">{{ t('common.loading') }}</p>

    <!-- 未关帐提示 -->
    <div
      v-if="noDataMessage && !data"
      class="bg-amber-50 border border-amber-300 rounded-sm p-4 mb-4 text-amber-800 text-sm"
    >
      ⚠️ {{ noDataMessage }}
    </div>

    <!-- 资产负债表 -->
    <div
      v-if="selectedReport === 'balance' && data"
      class="print-area bg-white shadow-sm px-12 pt-8 pb-4 max-w-[96%] mx-auto"
    >
      <h1 class="text-2xl font-bold text-center mb-4">{{ t('accounting.prints_page.balanceSheet') }}</h1>
      <div class="flex justify-between text-sm text-gray-600 mb-4">
        <span>{{ data.date_display }}</span>
        <span>金额单位：元</span>
      </div>
      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400">
            <th class="text-center py-1.5 px-2 font-bold bg-stone-50 border border-stone-200" style="text-align: center; width: 24%">
              {{ t('reports.assets') }}
            </th>
            <th
              class="text-center py-1.5 px-2 font-bold bg-stone-50 border border-stone-200"
              style="text-align: center; width: 13%"
            >
              {{ t('accounting.gl_page.endingBalance') }}
            </th>
            <th
              class="text-center py-1.5 px-2 font-bold bg-stone-50 border border-stone-200"
              style="text-align: center; width: 13%"
            >
              年初余额
            </th>
            <th class="text-center py-1.5 px-2 font-bold bg-stone-50 border border-stone-200" style="text-align: center; width: 24%">
              负债及所有者权益
            </th>
            <th
              class="text-center py-1.5 px-2 font-bold bg-stone-50 border border-stone-200"
              style="text-align: center; width: 13%"
            >
              {{ t('accounting.gl_page.endingBalance') }}
            </th>
            <th
              class="text-center py-1.5 px-2 font-bold bg-stone-50 border border-stone-200"
              style="text-align: center; width: 13%"
            >
              年初余额
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in Math.max(data.left_items?.length || 0, data.right_items?.length || 0)" :key="i">
            <td
              v-if="data.left_items?.[i - 1]"
              class="py-1.5 px-2 border border-stone-200"
              :class="{
                'font-bold bg-stone-50':
                  data.left_items[i - 1].name.includes('合计') || data.left_items[i - 1].name.includes('总计'),
              }"
            >
              {{ data.left_items[i - 1].name }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td
              v-if="data.left_items?.[i - 1]"
              class="report-number py-1.5 px-2 border border-stone-200"
              :class="{
                'font-bold bg-stone-50':
                  data.left_items[i - 1].name.includes('合计') || data.left_items[i - 1].name.includes('总计'),
              }"
            >
              {{ formatNumber(data.left_items[i - 1].ending) }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td
              v-if="data.left_items?.[i - 1]"
              class="report-number py-1.5 px-2 border border-stone-200"
              :class="{
                'font-bold bg-stone-50':
                  data.left_items[i - 1].name.includes('合计') || data.left_items[i - 1].name.includes('总计'),
              }"
            >
              {{ formatNumber(data.left_items[i - 1].beginning) }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td
              v-if="data.right_items?.[i - 1]"
              class="py-1.5 px-2 border border-stone-200"
              :class="{
                'font-bold bg-stone-50':
                  data.right_items[i - 1].name.includes('合计') || data.right_items[i - 1].name.includes('总计'),
              }"
            >
              {{ data.right_items[i - 1].name }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td
              v-if="data.right_items?.[i - 1]"
              class="report-number py-1.5 px-2 border border-stone-200"
              :class="{
                'font-bold bg-stone-50':
                  data.right_items[i - 1].name.includes('合计') || data.right_items[i - 1].name.includes('总计'),
              }"
            >
              {{ formatNumber(data.right_items[i - 1].ending) }}
            </td>
            <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            <td
              v-if="data.right_items?.[i - 1]"
              class="report-number py-1.5 px-2 border border-stone-200"
              :class="{
                'font-bold bg-stone-50':
                  data.right_items[i - 1].name.includes('合计') || data.right_items[i - 1].name.includes('总计'),
              }"
            >
              {{ formatNumber(data.right_items[i - 1].beginning) }}
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
    <div
      v-if="selectedReport === 'income' && data"
      class="print-area bg-white shadow-sm px-12 pt-8 pb-4 max-w-5xl mx-auto"
    >
      <h1 class="text-2xl font-bold text-center mb-4">{{ t('accounting.prints_page.incomeStatement') }}</h1>
      <div class="flex justify-between text-sm text-gray-600 mb-4">
        <span>{{ data.period_display }}</span>
        <span>金额单位：元</span>
      </div>
      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400 bg-stone-50">
            <th class="text-center py-1.5 px-2 border border-stone-200" style="text-align: center; width: 50%">项目</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="text-align: center; width: 17%">本期金额</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="text-align: center; width: 17%">本年累计</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="text-align: center; width: 17%">上年同期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in data.items" :key="item.name">
            <td
              class="py-1.5 px-2 border border-stone-200"
              :class="{
                'font-bold bg-stone-50':
                  item.name.includes('营业利润') || item.name.includes('利润总额') || item.name.includes('净利润'),
              }"
            >
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
    <div
      v-if="selectedReport === 'cashflow' && data"
      class="print-area bg-white shadow-sm px-12 pt-8 pb-4 max-w-5xl mx-auto"
    >
      <h1 class="text-2xl font-bold text-center mb-4">{{ t('accounting.prints_page.cashflowStatement') }}</h1>
      <div class="flex justify-between text-sm text-gray-600 mb-4">
        <span>{{ data.date_display }}</span>
        <span>金额单位：元</span>
      </div>
      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400 bg-stone-50">
            <th class="text-center py-1.5 px-2 border border-stone-200" style="text-align: center; width: 50%">项目</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="text-align: center; width: 17%">本期</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="text-align: center; width: 17%">本年累计</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="text-align: center; width: 17%">去年同期</th>
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
  @page {
    size: A4 portrait;
    margin: 10mm;
  }
  body * {
    visibility: hidden;
  }
  .print-area,
  .print-area * {
    visibility: visible;
  }
  .print-area {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    margin: 0 auto;
  }
}
</style>
