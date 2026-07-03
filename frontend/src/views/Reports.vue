<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import { getBalanceSheet, getIncomeStatement, getCashFlow } from '@/api'

const activeReport = ref('balance')
const currentPeriod = ref(new Date().toISOString().slice(0, 7))
const balanceData = ref<any>(null)
const incomeData = ref<any>(null)
const cashFlowData = ref<any>(null)
const loading = ref(false)
const COMPANY_NAME = '华安麦逄人工智能 MiphamAI'

function formatNumber(val: number | null) {
  if (val === null || val === undefined) return ''
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadReport() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const [bs, is, cf] = await Promise.all([
      getBalanceSheet(cid, currentPeriod.value),
      getIncomeStatement(cid, currentPeriod.value),
      getCashFlow(cid, currentPeriod.value),
    ])
    balanceData.value = bs.data
    incomeData.value = is.data
    cashFlowData.value = cf.data
  } catch (e: any) {
    alert(e.response?.data?.detail || '加载报表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadReport)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center">
        <input
          v-model="currentPeriod"
          type="month"
          class="px-3 py-2 border border-zinc-300 rounded-sm text-sm focus:ring-1 focus:ring-zinc-400 outline-none"
          @change="loadReport"
        />
        <Button label="刷新" icon="pi pi-refresh" text @click="loadReport" :loading="loading" />
      </div>
    </div>

    <div class="flex gap-1 mb-6">
      <Button
        label="资产负债表"
        :severity="activeReport === 'balance' ? 'danger' : 'secondary'"
        :text="activeReport !== 'balance'"
        @click="activeReport = 'balance'"
      />
      <Button
        label="利润表"
        :severity="activeReport === 'income' ? 'danger' : 'secondary'"
        :text="activeReport !== 'income'"
        @click="activeReport = 'income'"
      />
      <Button
        label="现金流量表"
        :severity="activeReport === 'cashflow' ? 'danger' : 'secondary'"
        :text="activeReport !== 'cashflow'"
        @click="activeReport = 'cashflow'"
      />
    </div>

    <p v-if="loading" class="text-zinc-400 text-sm tracking-wide">加载中...</p>

    <!-- ═══════ 资产负债表 会企01表 ═══════ -->
    <div v-if="activeReport === 'balance' && balanceData" class="print-area">
      <div class="report-container bg-white shadow-sm px-12 pt-6 pb-4 max-w-[96%] mx-auto">
        <h1 class="text-2xl font-bold text-center mb-4">资产负债表</h1>
        <div class="flex justify-between text-sm text-stone-500 mb-4">
          <span>公司名称：{{ COMPANY_NAME }}</span>
          <span>{{ balanceData.date_display }}</span>
          <span>金额单位：元</span>
        </div>

        <table class="data-table border-collapse border border-stone-300">
          <thead>
            <tr class="border-b-2 border-stone-400">
              <th class="text-left py-1.5 px-2 font-bold bg-stone-50 border border-stone-200" style="width: 30%">
                资 产
              </th>
              <th
                class="text-right py-1.5 px-2 font-bold bg-stone-50 border border-stone-200 report-number"
                style="width: 12%"
              >
                期末余额
              </th>
              <th
                class="text-right py-1.5 px-2 font-bold bg-stone-50 border border-stone-200 report-number"
                style="width: 12%"
              >
                年初余额
              </th>
              <th class="text-left py-1.5 px-2 font-bold bg-stone-50 border border-stone-200" style="width: 30%">
                负债及所有者权益
              </th>
              <th
                class="text-right py-1.5 px-2 font-bold bg-stone-50 border border-stone-200 report-number"
                style="width: 12%"
              >
                期末余额
              </th>
              <th
                class="text-right py-1.5 px-2 font-bold bg-stone-50 border border-stone-200 report-number"
                style="width: 12%"
              >
                年初余额
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="i in Math.max(balanceData.left_items?.length || 0, balanceData.right_items?.length || 0)"
              :key="i"
            >
              <td
                v-if="balanceData.left_items?.[i - 1]"
                class="py-1.5 px-2 border border-stone-200"
                :class="{
                  'font-bold bg-stone-50':
                    balanceData.left_items[i - 1].name.includes('合计') ||
                    balanceData.left_items[i - 1].name.includes('总计'),
                }"
              >
                {{ balanceData.left_items[i - 1].name }}
              </td>
              <td v-else class="py-1.5 px-2 border border-stone-200"></td>
              <td
                v-if="balanceData.left_items?.[i - 1]"
                class="report-number py-1.5 px-2 border border-stone-200"
                :class="{
                  'font-bold bg-stone-50':
                    balanceData.left_items[i - 1].name.includes('合计') ||
                    balanceData.left_items[i - 1].name.includes('总计'),
                }"
              >
                {{ formatNumber(balanceData.left_items[i - 1].ending) }}
              </td>
              <td v-else class="py-1.5 px-2 border border-stone-200"></td>
              <td
                v-if="balanceData.left_items?.[i - 1]"
                class="report-number py-1.5 px-2 border border-stone-200"
                :class="{
                  'font-bold bg-stone-50':
                    balanceData.left_items[i - 1].name.includes('合计') ||
                    balanceData.left_items[i - 1].name.includes('总计'),
                }"
              >
                {{ formatNumber(balanceData.left_items[i - 1].beginning) }}
              </td>
              <td v-else class="py-1.5 px-2 border border-stone-200"></td>
              <td
                v-if="balanceData.right_items?.[i - 1]"
                class="py-1.5 px-2 border border-stone-200"
                :class="{
                  'font-bold bg-stone-50':
                    balanceData.right_items[i - 1].name.includes('合计') ||
                    balanceData.right_items[i - 1].name.includes('总计'),
                }"
              >
                {{ balanceData.right_items[i - 1].name }}
              </td>
              <td v-else class="py-1.5 px-2 border border-stone-200"></td>
              <td
                v-if="balanceData.right_items?.[i - 1]"
                class="report-number py-1.5 px-2 border border-stone-200"
                :class="{
                  'font-bold bg-stone-50':
                    balanceData.right_items[i - 1].name.includes('合计') ||
                    balanceData.right_items[i - 1].name.includes('总计'),
                }"
              >
                {{ formatNumber(balanceData.right_items[i - 1].ending) }}
              </td>
              <td v-else class="py-1.5 px-2 border border-stone-200"></td>
              <td
                v-if="balanceData.right_items?.[i - 1]"
                class="report-number py-1.5 px-2 border border-stone-200"
                :class="{
                  'font-bold bg-stone-50':
                    balanceData.right_items[i - 1].name.includes('合计') ||
                    balanceData.right_items[i - 1].name.includes('总计'),
                }"
              >
                {{ formatNumber(balanceData.right_items[i - 1].beginning) }}
              </td>
              <td v-else class="py-1.5 px-2 border border-stone-200"></td>
            </tr>
          </tbody>
        </table>

        <div class="flex justify-between text-sm text-stone-500 mt-4 pt-3 border-t border-stone-300">
          <span>公司负责人：</span>
          <span>财务负责人：</span>
          <span>制表人：&emsp;&emsp;&emsp;</span>
        </div>
      </div>
    </div>

    <!-- ═══════ 利润表 会企02表 ═══════ -->
    <div v-if="activeReport === 'income' && incomeData" class="print-area">
      <div class="report-container bg-white shadow-sm px-12 pt-6 pb-4 max-w-5xl mx-auto">
        <h1 class="text-2xl font-bold text-center mb-4">利润表</h1>
        <div class="flex justify-between text-sm text-stone-500 mb-4">
          <span>公司名称：{{ COMPANY_NAME }}</span>
          <span>{{ incomeData.period_display }}</span>
          <span>金额单位：元</span>
        </div>

        <table class="data-table border-collapse border border-stone-300">
          <thead>
            <tr class="border-b-2 border-stone-400 bg-stone-50">
              <th class="text-left py-1.5 px-2 font-bold border border-stone-200" style="width: 50%">项 目</th>
              <th class="text-right py-1.5 px-2 font-bold border border-stone-200 report-number" style="width: 17%">
                本月金额
              </th>
              <th class="text-right py-1.5 px-2 font-bold border border-stone-200 report-number" style="width: 17%">
                本年累计金额
              </th>
              <th class="text-right py-1.5 px-2 font-bold border border-stone-200 report-number" style="width: 17%">
                上年同期累计
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in incomeData.items" :key="item.name">
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

        <div class="flex justify-between text-sm text-stone-500 mt-4 pt-3 border-t border-stone-300">
          <span>公司负责人：</span>
          <span>财务负责人：</span>
          <span>制表人：&emsp;&emsp;&emsp;</span>
        </div>
      </div>
    </div>

    <!-- ═══════ 现金流量表 会企03表 ═══════ -->
    <div v-if="activeReport === 'cashflow' && cashFlowData" class="print-area">
      <div class="report-container bg-white shadow-sm px-12 pt-6 pb-4 max-w-5xl mx-auto">
        <h1 class="text-2xl font-bold text-center mb-4">现金流量表</h1>
        <div class="flex justify-between text-sm text-stone-500 mb-4">
          <span>公司名称：{{ COMPANY_NAME }}</span>
          <span>{{ cashFlowData.date_display }}</span>
          <span>金额单位：元</span>
        </div>

        <table class="data-table border-collapse border border-stone-300">
          <thead>
            <tr class="border-b-2 border-stone-400 bg-stone-50">
              <th class="text-left py-1.5 px-2 font-bold border border-stone-200" style="width: 50%">项 目</th>
              <th class="text-right py-1.5 px-2 font-bold border border-stone-200 report-number" style="width: 17%">
                本月金额
              </th>
              <th class="text-right py-1.5 px-2 font-bold border border-stone-200 report-number" style="width: 17%">
                本年累计金额
              </th>
              <th class="text-right py-1.5 px-2 font-bold border border-stone-200 report-number" style="width: 17%">
                上年同期累计
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in cashFlowData.rows" :key="idx">
              <td class="py-1.5 px-2 border border-stone-200">{{ row[0] }}</td>
              <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(row[1]) }}</td>
              <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(row[2]) }}</td>
              <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(row[3]) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="flex justify-between text-sm text-stone-500 mt-4 pt-3 border-t border-stone-300">
          <span>公司负责人：</span>
          <span>财务负责人：</span>
          <span>制表人：&emsp;&emsp;&emsp;</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media print {
  @page {
    size: A4;
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
  }
  .report-container {
    margin: 0 auto;
    page-break-inside: avoid;
  }
}
</style>
