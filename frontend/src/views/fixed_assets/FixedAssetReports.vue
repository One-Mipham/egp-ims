<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from '@/i18n'
import { listFixedAssets } from '../../api'

const { t } = useI18n()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])

const summary = computed(() => {
  const data = items.value
  return {
    count: data.length,
    totalOriginal: data.reduce((s: number, i: any) => s + (i.original_value || 0), 0),
    totalDepreciation: data.reduce((s: number, i: any) => s + (i.accumulated_depreciation || 0), 0),
    totalNet: data.reduce((s: number, i: any) => s + (i.net_value || 0), 0),
  }
})

const categoryGroups = computed(() => {
  const map: Record<string, any[]> = {}
  for (const item of items.value) {
    const cat = item.category || '其他'
    if (!map[cat]) map[cat] = []
    map[cat].push(item)
  }
  return Object.entries(map).map(([cat, list]) => ({
    category: cat,
    count: list.length,
    totalOriginal: list.reduce((s, i) => s + (i.original_value || 0), 0),
    totalDepreciation: list.reduce((s, i) => s + (i.accumulated_depreciation || 0), 0),
    totalNet: list.reduce((s, i) => s + (i.net_value || 0), 0),
    depreciationRate:
      list.reduce((s, i) => s + (i.original_value || 0), 0) > 0
        ? (
            (list.reduce((s, i) => s + (i.accumulated_depreciation || 0), 0) /
              list.reduce((s, i) => s + (i.original_value || 0), 0)) *
            100
          ).toFixed(1)
        : '0.0',
  }))
})

const statusGroups = computed(() => {
  const map: Record<string, number> = {}
  for (const item of items.value) {
    const s = item.status || '未知'
    map[s] = (map[s] || 0) + 1
  }
  return Object.entries(map)
})

async function load() {
  const { data } = await listFixedAssets(companyId)
  items.value = data
}

onMounted(load)

function exportCSV() {
  const header = ['资产编号', '名称', '类别', '原值', '累计折旧', '净值', '状态']
  const rows = items.value.map((i: any) => [
    i.asset_code,
    i.name,
    i.category,
    i.original_value,
    i.accumulated_depreciation,
    i.net_value,
    i.status,
  ])
  const csv = [
    header.join(','),
    ...rows.map((r: any[]) => r.map((c: any) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')),
  ].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '固定资产报表.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">资产报表</h1>
      <button @click="exportCSV" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">导出CSV</button>
    </div>

    <div class="grid grid-cols-4 gap-3 mb-6">
      <div class="bg-blue-50 rounded p-4 text-center">
        <div class="text-xs text-blue-600 mb-1">资产总数</div>
        <div class="text-2xl font-bold text-blue-700">{{ summary.count }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">原值合计</div>
        <div class="text-2xl font-bold">{{ summary.totalOriginal.toLocaleString() }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">{{ t('assets.accumulatedDepreciation') }}</div>
        <div class="text-2xl font-bold text-amber-600">{{ summary.totalDepreciation.toLocaleString() }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">净值合计</div>
        <div class="text-2xl font-bold text-green-600">{{ summary.totalNet.toLocaleString() }}</div>
      </div>
    </div>

    <h2 class="text-base font-bold mb-3">按类别汇总</h2>
    <table class="w-full text-sm border-collapse mb-6">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">{{ t('assets.assetCategory') }}</th>
          <th class="p-2 border text-right">数量</th>
          <th class="p-2 border text-right">{{ t('assets.originalValue') }}</th>
          <th class="p-2 border text-right">{{ t('assets.accumulatedDepreciation') }}</th>
          <th class="p-2 border text-right">{{ t('assets.netValue') }}</th>
          <th class="p-2 border text-right">折旧率</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="g in categoryGroups" :key="g.category" class="hover:bg-zinc-50">
          <td class="p-2 border font-medium">{{ g.category }}</td>
          <td class="p-2 border text-right">{{ g.count }}</td>
          <td class="p-2 border text-right">{{ g.totalOriginal.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ g.totalDepreciation.toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold">{{ g.totalNet.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ g.depreciationRate }}%</td>
        </tr>
      </tbody>
    </table>

    <h2 class="text-base font-bold mb-3">按状态分布</h2>
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">{{ t('common.status') }}</th>
          <th class="p-2 border text-right">数量</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="[status, count] in statusGroups" :key="status" class="hover:bg-zinc-50">
          <td class="p-2 border">{{ status }}</td>
          <td class="p-2 border text-right">{{ count }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
