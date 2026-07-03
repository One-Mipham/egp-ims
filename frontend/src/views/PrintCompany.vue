<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import { printCompany } from '@/api'

const company = ref<any>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await printCompany(cid)
    company.value = res.data
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
      <Button label="打印" icon="pi pi-print" @click="doPrint" :disabled="!company" />
    </div>

    <p v-if="loading" class="text-zinc-400 text-sm">加载中...</p>

    <div v-if="company" class="print-area bg-white shadow-sm px-12 pt-8 pb-6 max-w-4xl mx-auto">
      <h1 class="text-2xl font-bold text-center mb-6">公司信息</h1>
      <div class="flex justify-between text-sm text-gray-600 mb-6">
        <span>公司名称：{{ company.name }}</span>
        <span>金额单位：{{ company.currency }}</span>
      </div>

      <table class="data-table border-collapse border border-stone-300 max-w-lg">
        <tbody>
          <tr class="border-b border-stone-200">
            <td class="py-2 px-3 font-medium bg-stone-50 w-36 border border-stone-200 text-xs uppercase tracking-wider">
              公司名称
            </td>
            <td class="py-2 px-3 border border-stone-200">{{ company.name }}</td>
          </tr>
          <tr class="border-b border-stone-200">
            <td class="py-2 px-3 font-medium bg-stone-50 border border-stone-200 text-xs uppercase tracking-wider">
              简称
            </td>
            <td class="py-2 px-3 border border-stone-200">{{ company.short_name || '-' }}</td>
          </tr>
          <tr class="border-b border-stone-200">
            <td class="py-2 px-3 font-medium bg-stone-50 border border-stone-200 text-xs uppercase tracking-wider">
              行业
            </td>
            <td class="py-2 px-3 border border-stone-200">{{ company.industry }}</td>
          </tr>
          <tr class="border-b border-stone-200">
            <td class="py-2 px-3 font-medium bg-stone-50 border border-stone-200 text-xs uppercase tracking-wider">
              币种
            </td>
            <td class="py-2 px-3 border border-stone-200">{{ company.currency }}</td>
          </tr>
          <tr class="border-b border-stone-200">
            <td class="py-2 px-3 font-medium bg-stone-50 border border-stone-200 text-xs uppercase tracking-wider">
              会计年度起始
            </td>
            <td class="py-2 px-3 border border-stone-200">{{ company.fiscal_year_start }}</td>
          </tr>
          <tr class="border-b border-stone-200">
            <td class="py-2 px-3 font-medium bg-stone-50 border border-stone-200 text-xs uppercase tracking-wider">
              内控模式
            </td>
            <td class="py-2 px-3 border border-stone-200">{{ company.internal_control_mode }}</td>
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
