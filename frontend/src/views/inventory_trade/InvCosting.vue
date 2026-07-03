<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listInvStock } from '../../api'

const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])

const summary = computed(() => ({
  count: items.value.length,
  totalQty: items.value.reduce((s: number, i: any) => s + (i.quantity || 0), 0),
  totalCost: items.value.reduce((s: number, i: any) => s + (i.total_cost || 0), 0),
}))

const categoryCosting = computed(() => {
  const map: Record<string, any[]> = {}
  for (const item of items.value) {
    const cat = item.category || '未分类'
    if (!map[cat]) map[cat] = []
    map[cat].push(item)
  }
  return Object.entries(map).map(([cat, list]) => ({
    category: cat,
    count: list.length,
    totalQty: list.reduce((s, i) => s + (i.quantity || 0), 0),
    totalCost: list.reduce((s, i) => s + (i.total_cost || 0), 0),
    avgUnitCost:
      list.reduce((s, i) => s + (i.quantity || 0), 0) > 0
        ? list.reduce((s, i) => s + (i.total_cost || 0), 0) / list.reduce((s, i) => s + (i.quantity || 0), 0)
        : 0,
    items: list,
  }))
})

const warehouseCosting = computed(() => {
  const map: Record<string, any[]> = {}
  for (const item of items.value) {
    const wh = item.warehouse || '默认仓库'
    if (!map[wh]) map[wh] = []
    map[wh].push(item)
  }
  return Object.entries(map).map(([wh, list]) => ({
    warehouse: wh,
    count: list.length,
    totalCost: list.reduce((s, i) => s + (i.total_cost || 0), 0),
  }))
})

async function load() {
  const { data } = await listInvStock(companyId)
  items.value = data
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <h1 class="text-lg font-bold mb-4">成本核算</h1>

    <div class="grid grid-cols-3 gap-3 mb-6">
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">库存品类</div>
        <div class="text-2xl font-bold">{{ summary.count }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">库存总量</div>
        <div class="text-2xl font-bold">{{ summary.totalQty.toLocaleString() }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">库存总成本</div>
        <div class="text-2xl font-bold text-blue-700">{{ summary.totalCost.toLocaleString() }}</div>
      </div>
    </div>

    <h2 class="text-base font-bold mb-3">按类别核算</h2>
    <table class="w-full text-sm border-collapse mb-6">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">类别</th>
          <th class="p-2 border text-right">品类数</th>
          <th class="p-2 border text-right">总数量</th>
          <th class="p-2 border text-right">总成本</th>
          <th class="p-2 border text-right">加权平均单价</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="g in categoryCosting" :key="g.category" class="hover:bg-zinc-50">
          <td class="p-2 border font-medium">{{ g.category }}</td>
          <td class="p-2 border text-right">{{ g.count }}</td>
          <td class="p-2 border text-right">{{ g.totalQty.toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold">{{ g.totalCost.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ g.avgUnitCost.toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>

    <h2 class="text-base font-bold mb-3">按仓库核算</h2>
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">仓库</th>
          <th class="p-2 border text-right">品类数</th>
          <th class="p-2 border text-right">总成本</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="w in warehouseCosting" :key="w.warehouse" class="hover:bg-zinc-50">
          <td class="p-2 border">{{ w.warehouse }}</td>
          <td class="p-2 border text-right">{{ w.count }}</td>
          <td class="p-2 border text-right font-bold">{{ w.totalCost.toLocaleString() }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
