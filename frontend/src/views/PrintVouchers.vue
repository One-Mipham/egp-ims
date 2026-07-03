<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import { printVouchers, listAccounts } from '@/api'

const data = ref<any>(null)
const accounts = ref<any[]>([])
const loading = ref(false)
const selectedRange = ref('month')
const RANGE_OPTIONS = [
  { label: '当日凭证', value: 'today' },
  { label: '本周凭证', value: 'week' },
  { label: '本月凭证', value: 'month' },
]

const TYPE_LABELS: Record<string, string> = { receipt: '收款凭证', payment: '付款凭证', transfer: '转账凭证' }

const accountMap = computed(() => {
  const m: Record<string, string> = {}
  for (const a of accounts.value) m[a.code] = a.name
  return m
})

function formatNumber(val: number | null) {
  if (val === null || val === undefined) return ''
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function entryTotal(entries: any[], field: string) {
  return formatNumber(entries.reduce((s: number, e: any) => s + (e[field] || 0), 0))
}

function hasAuxData(v: any) {
  return v.entries.some((e: any) => e.department_name || e.person_name || e.counterparty_name)
}

function auxLabel(e: any) {
  const parts = []
  if (e.department_name) parts.push(e.department_name)
  if (e.person_name) parts.push(e.person_name)
  if (e.counterparty_name) parts.push(e.counterparty_name)
  if (e.project_name) parts.push(e.project_name)
  return parts.join('/')
}

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const [vRes, aRes] = await Promise.all([printVouchers(cid, selectedRange.value), listAccounts(cid)])
    data.value = vRes.data
    accounts.value = aRes.data
  } catch (e: any) {
    alert(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function doPrint() {
  window.print()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4 no-print">
      <div class="flex gap-2 items-center">
        <Dropdown
          v-model="selectedRange"
          :options="RANGE_OPTIONS"
          optionLabel="label"
          optionValue="value"
          class="w-40"
          @change="load"
        />
        <Button label="打印" icon="pi pi-print" @click="doPrint" :disabled="!data?.vouchers?.length" />
      </div>
    </div>

    <p v-if="loading" class="text-zinc-400 text-sm">加载中...</p>
    <p v-if="data && !data.vouchers.length" class="text-zinc-400 text-sm">该期间内无凭证</p>

    <div v-if="data?.vouchers?.length" class="print-area">
      <div v-for="v in data.vouchers" :key="v.id" class="voucher-page">
        <!-- Header -->
        <h1 class="voucher-title">{{ TYPE_LABELS[v.voucher_type] || '记账凭证' }}</h1>
        <div class="voucher-meta">
          <span>{{ v.date }}</span>
          <span>{{ v.voucher_no }}</span>
          <span>附单据 张</span>
        </div>

        <!-- Table -->
        <table class="voucher-table">
          <thead>
            <tr>
              <th class="col-summary">摘&emsp;要</th>
              <th class="col-account">科&emsp;目</th>
              <th class="col-debit">借方金额</th>
              <th class="col-credit">贷方金额</th>
              <th v-if="hasAuxData(v)" class="col-aux">辅助核算</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(e, idx) in v.entries" :key="idx">
              <td class="col-summary">{{ e.description || v.summary }}</td>
              <td class="col-account">{{ e.account_code }} {{ accountMap[e.account_code] || '' }}</td>
              <td class="col-debit">{{ formatNumber(e.debit) }}</td>
              <td class="col-credit">{{ formatNumber(e.credit) }}</td>
              <td v-if="hasAuxData(v)" class="col-aux">{{ auxLabel(e) }}</td>
            </tr>
            <tr class="total-row">
              <td class="col-summary">合&emsp;计</td>
              <td class="col-account">&yen; 人民币</td>
              <td class="col-debit">{{ entryTotal(v.entries, 'debit') }}</td>
              <td class="col-credit">{{ entryTotal(v.entries, 'credit') }}</td>
              <td v-if="hasAuxData(v)" class="col-aux" />
            </tr>
          </tbody>
        </table>

        <!-- Signatures -->
        <div class="voucher-footer">
          <span>制单人：__________</span>
          <span>审核人：__________</span>
          <span>记账人：__________</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.voucher-page {
  background: white;
  padding: 2rem 1.5rem 1.5rem;
  margin: 0 auto 20mm;
  max-width: 190mm;
  font-size: 10.5pt;
  line-height: 1.6;
}

.voucher-title {
  text-align: center;
  font-size: 14pt;
  font-weight: bold;
  margin-bottom: 0.25rem;
  letter-spacing: 0.3em;
}

.voucher-meta {
  display: flex;
  justify-content: flex-end;
  gap: 2rem;
  font-size: 9.5pt;
  color: #444;
  margin-bottom: 0.75rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #ccc;
}

.voucher-table {
  width: 100%;
  border-collapse: collapse;
  border: 1.5px solid #333;
}

.voucher-table th,
.voucher-table td {
  border: 0.5px solid #666;
  padding: 3px 6px;
  font-size: 10pt;
}

.voucher-table thead th {
  background: #f5f5f5;
  font-weight: 600;
  text-align: center;
  padding: 5px 6px;
  border-bottom: 1.5px solid #333;
}

.voucher-table .col-summary {
  width: 30%;
  text-align: left;
}

.voucher-table .col-account {
  text-align: left;
}

.voucher-table .col-debit,
.voucher-table .col-credit {
  width: 14%;
  text-align: right;
  font-family: 'SF Mono', 'Menlo', 'Consolas', 'Courier New', monospace;
  font-variant-numeric: tabular-nums;
}

.voucher-table .col-aux {
  width: 14%;
  text-align: left;
  font-size: 9pt;
}

.voucher-table .total-row td {
  font-weight: bold;
  border-top: 1.5px solid #333;
  background: #fafafa;
}

.voucher-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  padding-top: 0.5rem;
  font-size: 9.5pt;
  color: #444;
  letter-spacing: 0.1em;
}

.no-print {
  display: flex;
}

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
  }
  .no-print {
    display: none !important;
  }
}
</style>
