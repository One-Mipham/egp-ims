<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listReceivables, getReceivablesSummary } from '../../api'

const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const summary = ref<any>(null)

const agingBuckets = computed(() => {
  const buckets = [
    { label: '未到期', min: -Infinity, max: 0, color: 'text-green-600', bg: 'bg-green-50' },
    { label: '1-30 天', min: 1, max: 30, color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: '31-60 天', min: 31, max: 60, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: '61-90 天', min: 61, max: 90, color: 'text-red-500', bg: 'bg-red-50' },
    { label: '90 天以上', min: 91, max: Infinity, color: 'text-red-700', bg: 'bg-red-100' },
  ]
  return buckets.map(b => {
    const matched = items.value.filter((i: any) => i.balance > 0 && i.aging_days >= b.min && i.aging_days <= b.max)
    return {
      ...b,
      count: matched.length,
      total: matched.reduce((s: number, i: any) => s + (i.balance || 0), 0),
    }
  })
})

const totalBalance = computed(() => items.value.reduce((s: number, i: any) => s + (i.balance || 0), 0))
const totalCount = computed(() => items.value.filter((i: any) => i.balance > 0).length)

onMounted(async () => {
  const [invRes, sumRes] = await Promise.all([
    listReceivables(companyId, { limit: 500 }),
    getReceivablesSummary(companyId),
  ])
  items.value = invRes.data
  summary.value = sumRes.data
})
</script>

<template>
  <div class="p-4">
    <h1 class="text-lg font-bold mb-4">应收账款账龄分析</h1>

    <div class="grid grid-cols-4 gap-3 mb-4">
      <div class="bg-blue-50 rounded p-4 text-center">
        <div class="text-xs text-blue-600 mb-1">未收发票数</div>
        <div class="text-2xl font-bold text-blue-700">{{ summary?.invoice_count ?? totalCount }}</div>
      </div>
      <div class="bg-zinc-50 rounded p-4 text-center">
        <div class="text-xs text-zinc-500 mb-1">应收余额合计</div>
        <div class="text-2xl font-bold text-red-600">{{ (summary?.total_ar ?? totalBalance).toLocaleString() }}</div>
      </div>
      <div class="bg-red-50 rounded p-4 text-center">
        <div class="text-xs text-red-500 mb-1">坏账笔数</div>
        <div class="text-2xl font-bold text-red-700">{{ summary?.bad_debt_count ?? 0 }}</div>
      </div>
      <div class="bg-red-50 rounded p-4 text-center">
        <div class="text-xs text-red-500 mb-1">坏账金额</div>
        <div class="text-2xl font-bold text-red-700">{{ (summary?.bad_debt_amount ?? 0).toLocaleString() }}</div>
      </div>
    </div>

    <div class="grid grid-cols-5 gap-2 mb-6">
      <div v-for="b in agingBuckets" :key="b.label" :class="[b.bg, 'rounded p-3 text-center']">
        <div class="text-xs text-zinc-500 mb-1">{{ b.label }}</div>
        <div :class="[b.color, 'text-lg font-bold']">{{ b.total.toLocaleString() }}</div>
        <div class="text-xs text-zinc-400">{{ b.count }} 笔</div>
      </div>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">客户</th>
          <th class="p-2 border">发票号</th>
          <th class="p-2 border text-right">金额</th>
          <th class="p-2 border text-right">余额</th>
          <th class="p-2 border">到期日</th>
          <th class="p-2 border text-right">账龄(天)</th>
          <th class="p-2 border">状态</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in items"
          :key="item.id"
          v-show="item.balance > 0"
          class="hover:bg-zinc-50"
          :class="(item.aging_days || 0) > 90 ? 'bg-red-50' : (item.aging_days || 0) > 60 ? 'bg-orange-50' : ''"
        >
          <td class="p-2 border">{{ item.customer_name }}</td>
          <td class="p-2 border font-mono text-xs">{{ item.invoice_no }}</td>
          <td class="p-2 border text-right">{{ (item.amount || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold" :class="(item.aging_days || 0) > 90 ? 'text-red-700' : ''">
            {{ (item.balance || 0).toLocaleString() }}
          </td>
          <td class="p-2 border text-xs">{{ item.due_date }}</td>
          <td
            class="p-2 border text-right font-bold"
            :class="(item.aging_days || 0) > 90 ? 'text-red-600' : (item.aging_days || 0) > 60 ? 'text-orange-600' : ''"
          >
            {{ item.aging_days }}
          </td>
          <td class="p-2 border">{{ item.status }}</td>
        </tr>
        <tr v-if="totalCount === 0">
          <td colspan="7" class="p-6 text-center text-green-600 text-sm">所有应收账款已结清</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
