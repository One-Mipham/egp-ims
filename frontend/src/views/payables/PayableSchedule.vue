<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listPayables } from '../../api'

const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])

const scheduleByDate = computed(() => {
  const map: Record<string, any[]> = {}
  for (const item of items.value) {
    if (item.balance <= 0) continue
    const due = item.due_date || '未指定'
    if (!map[due]) map[due] = []
    map[due].push(item)
  }
  const entries = Object.entries(map)
  entries.sort(([a], [b]) => a.localeCompare(b))
  const result: any[] = []
  for (const [date, list] of entries) {
    result.push({
      date,
      count: list.length,
      total: list.reduce((s: number, i: any) => s + (i.balance || 0), 0),
      items: list,
    })
  }
  return result
})

const totalUpcoming = computed(() => {
  let sum = 0
  for (const group of scheduleByDate.value) {
    sum += group.total
  }
  return sum
})

const overdueTotal = computed(() =>
  items.value
    .filter((i: any) => i.balance > 0 && i.aging_days > 0)
    .reduce((s: number, i: any) => s + (i.balance || 0), 0),
)

async function load() {
  const { data } = await listPayables(companyId, { limit: 500 })
  items.value = data
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <h1 class="text-lg font-bold mb-4">付款计划</h1>

    <div class="grid grid-cols-3 gap-3 mb-6">
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">待付总额</div>
        <div class="text-2xl font-bold text-red-600">{{ totalUpcoming.toLocaleString() }}</div>
      </div>
      <div class="bg-amber-50 rounded p-4 text-center">
        <div class="text-xs text-amber-600 mb-1">已逾期</div>
        <div class="text-2xl font-bold text-amber-700">{{ overdueTotal.toLocaleString() }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">待付笔数</div>
        <div class="text-2xl font-bold">{{ scheduleByDate.reduce((s, g) => s + g.count, 0) }}</div>
      </div>
    </div>

    <div v-for="group in scheduleByDate" :key="group.date" class="mb-4">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-sm font-bold">{{ group.date }}</span>
        <span class="text-xs text-zinc-500">{{ group.count }} 笔 · {{ group.total.toLocaleString() }}</span>
      </div>
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="bg-zinc-50 text-left">
            <th class="p-2 border text-xs">供应商</th>
            <th class="p-2 border text-xs">发票号</th>
            <th class="p-2 border text-xs text-right">金额</th>
            <th class="p-2 border text-xs text-right">余额</th>
            <th class="p-2 border text-xs">状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in group.items" :key="item.id" class="hover:bg-zinc-50">
            <td class="p-2 border text-xs">{{ item.supplier_name }}</td>
            <td class="p-2 border text-xs font-mono">{{ item.invoice_no }}</td>
            <td class="p-2 border text-xs text-right">{{ (item.amount || 0).toLocaleString() }}</td>
            <td class="p-2 border text-xs text-right font-bold text-red-600">
              {{ (item.balance || 0).toLocaleString() }}
            </td>
            <td class="p-2 border text-xs">{{ item.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="scheduleByDate.length === 0" class="p-6 text-center text-green-600 text-sm">
      所有应付账款已结清，暂无待付款项。
    </div>
  </div>
</template>
