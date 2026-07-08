<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import { printGeneralLedger } from '@/api'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const data = ref<any>(null)
const loading = ref(false)
const currentPeriod = ref(new Date().toISOString().slice(0, 7))

function formatNumber(val: number | null) {
  if (val === null || val === undefined) return ''
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await printGeneralLedger(cid, currentPeriod.value)
    data.value = res.data
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
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center">
        <input
          v-model="currentPeriod"
          type="month"
          class="px-3 py-2 border border-zinc-300 rounded-sm text-sm"
          @change="load"
        />
        <Button :label="t('common.print')" icon="pi pi-print" @click="doPrint" :disabled="!data" />
      </div>
    </div>

    <p v-if="loading" class="text-zinc-400 text-sm">{{ t('common.loading') }}</p>

    <div v-if="data" class="print-area bg-white shadow-sm px-12 pt-8 pb-6 max-w-5xl mx-auto">
      <h1 class="text-2xl font-bold text-center mb-4">总账余额表</h1>
      <div class="flex justify-between text-sm text-gray-600 mb-4">
        <span>{{ t('accounting.periods_page.period') }}：{{ data.period }}</span>
        <span>金额单位：元</span>
      </div>

      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400 bg-stone-50">
            <th class="text-left py-1.5 px-2 border border-stone-200" style="width: 90px">{{ t('accounting.accounts_page.code') }}</th>
            <th class="text-left py-1.5 px-2 border border-stone-200">{{ t('accounting.accounts_page.name') }}</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number">{{ t('accounting.gl_page.beginningBalance') }}</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number">{{ t('accounting.gl_page.currentPeriodDebit') }}</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number">{{ t('accounting.gl_page.currentPeriodCredit') }}</th>
            <th class="text-right py-1.5 px-2 border border-stone-200 report-number">{{ t('accounting.gl_page.endingBalance') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in data.rows" :key="r.code" class="border-b border-stone-200 font-bold">
            <td class="py-1.5 px-2 border border-stone-200">{{ r.code }}</td>
            <td class="py-1.5 px-2 border border-stone-200">{{ r.name }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(r.beginning) }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(r.debit) }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(r.credit) }}</td>
            <td class="report-number py-1.5 px-2 border border-stone-200">{{ formatNumber(r.ending) }}</td>
          </tr>
        </tbody>
      </table>
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
