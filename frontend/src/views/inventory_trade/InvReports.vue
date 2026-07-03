<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listInvStock, listPurchases, listInvSales } from '../../api'

const companyId = Number(localStorage.getItem('companyId') || '1')
const stockItems = ref<any[]>([])
const purchaseItems = ref<any[]>([])
const salesItems = ref<any[]>([])

const summary = computed(() => {
  const totalValue = stockItems.value.reduce((s: number, i: any) => s + (i.total_cost || 0), 0)
  const totalQty = stockItems.value.reduce((s: number, i: any) => s + (i.quantity || 0), 0)
  const purchaseTotal = purchaseItems.value.reduce((s: number, i: any) => s + (i.total_amount || 0), 0)
  const salesTotal = salesItems.value.reduce((s: number, i: any) => s + (i.total_amount || 0), 0)
  const salesProfit = salesItems.value.reduce((s: number, i: any) => s + (i.profit || 0), 0)
  return { totalValue, totalQty, purchaseTotal, salesTotal, salesProfit }
})

const warehouseReport = computed(() => {
  const map: Record<string, any[]> = {}
  for (const item of stockItems.value) {
    const wh = item.warehouse || '默认仓库'
    if (!map[wh]) map[wh] = []
    map[wh].push(item)
  }
  return Object.entries(map).map(([wh, list]) => ({
    warehouse: wh,
    count: list.length,
    totalQty: list.reduce((s, i) => s + (i.quantity || 0), 0),
    totalValue: list.reduce((s, i) => s + (i.total_cost || 0), 0),
    lowStockCount: list.filter((i: any) => (i.quantity || 0) <= (i.min_stock || 0)).length,
  }))
})

const lowStockItems = computed(() => stockItems.value.filter((i: any) => (i.quantity || 0) <= (i.min_stock || 0)))

async function load() {
  const [r1, r2, r3] = await Promise.all([listInvStock(companyId), listPurchases(companyId), listInvSales(companyId)])
  stockItems.value = r1.data
  purchaseItems.value = r2.data
  salesItems.value = r3.data
}

onMounted(load)

function exportCSV() {
  const header = ['仓库', '品类数', '总数量', '总价值', '低库存数']
  const rows = warehouseReport.value.map((w: any) => [w.warehouse, w.count, w.totalQty, w.totalValue, w.lowStockCount])
  const csv = [
    header.join(','),
    ...rows.map((r: any[]) => r.map((c: any) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')),
  ].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '库存报表.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">库存报表</h1>
      <button @click="exportCSV" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">导出CSV</button>
    </div>

    <div class="grid grid-cols-5 gap-3 mb-6">
      <div class="bg-blue-50 rounded p-3 text-center">
        <div class="text-xs text-blue-600 mb-1">库存总值</div>
        <div class="text-lg font-bold text-blue-700">{{ summary.totalValue.toLocaleString() }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-3 text-center">
        <div class="text-xs text-zinc-500 mb-1">库存总量</div>
        <div class="text-lg font-bold">{{ summary.totalQty.toLocaleString() }}</div>
      </div>
      <div class="bg-green-50 rounded p-3 text-center">
        <div class="text-xs text-green-600 mb-1">采购总额</div>
        <div class="text-lg font-bold text-green-700">{{ summary.purchaseTotal.toLocaleString() }}</div>
      </div>
      <div class="bg-amber-50 rounded p-3 text-center">
        <div class="text-xs text-amber-600 mb-1">销售总额</div>
        <div class="text-lg font-bold text-amber-700">{{ summary.salesTotal.toLocaleString() }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-3 text-center">
        <div class="text-xs text-zinc-500 mb-1">销售毛利</div>
        <div class="text-lg font-bold" :class="summary.salesProfit >= 0 ? 'text-green-600' : 'text-red-600'">
          {{ summary.salesProfit.toLocaleString() }}
        </div>
      </div>
    </div>

    <div v-if="lowStockItems.length > 0" class="bg-red-50 border border-red-200 rounded p-3 mb-6">
      <h2 class="text-sm font-bold text-red-700 mb-2">低库存预警 ({{ lowStockItems.length }} 项)</h2>
      <div class="flex flex-wrap gap-2">
        <span v-for="item in lowStockItems" :key="item.id" class="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
          {{ item.product_name }}: {{ item.quantity }}{{ item.unit }} (最低 {{ item.min_stock }})
        </span>
      </div>
    </div>

    <h2 class="text-base font-bold mb-3">按仓库汇总</h2>
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">仓库</th>
          <th class="p-2 border text-right">品类数</th>
          <th class="p-2 border text-right">总数量</th>
          <th class="p-2 border text-right">总价值</th>
          <th class="p-2 border text-right">低库存</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="w in warehouseReport" :key="w.warehouse" class="hover:bg-zinc-50">
          <td class="p-2 border font-medium">{{ w.warehouse }}</td>
          <td class="p-2 border text-right">{{ w.count }}</td>
          <td class="p-2 border text-right">{{ w.totalQty.toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold">{{ w.totalValue.toLocaleString() }}</td>
          <td class="p-2 border text-right">
            <span v-if="w.lowStockCount > 0" class="text-red-600 font-bold">{{ w.lowStockCount }}</span>
            <span v-else class="text-green-600">0</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
