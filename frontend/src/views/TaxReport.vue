<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Calendar from 'primevue/calendar'
import { getDeclarationsSummary } from '@/api/taxes'

const route = useRoute()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const reportType = computed(() => {
  const p = route.path
  if (p.includes('/vat')) return 'vat'
  if (p.includes('/cit')) return 'cit'
  return 'other'
})

const title = computed(() => {
  if (reportType.value === 'vat') return '增值税申报表'
  if (reportType.value === 'cit') return '所得税申报表'
  return '其他税种申报汇总'
})

const summaries = ref<any[]>([])
const loading = ref(false)
const periodStart = ref<Date | null>(null)
const periodEnd = ref<Date | null>(null)

async function load() {
  loading.value = true
  try {
    const params: any = { company_id: companyId.value }
    if (periodStart.value) params.period_start = periodStart.value.toISOString().slice(0, 10)
    if (periodEnd.value) params.period_end = periodEnd.value.toISOString().slice(0, 10)
    const res = await getDeclarationsSummary(params)
    let data = res.data

    if (reportType.value === 'vat') {
      data = data.filter((s: any) => s.tax_type === 'vat')
    } else if (reportType.value === 'cit') {
      data = data.filter((s: any) => s.tax_type === 'corporate_income')
    }

    summaries.value = data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">{{ title }}</h2>
      <div class="flex gap-2">
        <Calendar v-model="periodStart" placeholder="期间起" showIcon class="w-36" />
        <Calendar v-model="periodEnd" placeholder="期间止" showIcon class="w-36" />
        <Button label="查询" icon="pi pi-search" severity="secondary" @click="load" />
      </div>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-4" v-if="!loading">
      <div class="bg-white rounded-sm border border-stone-200 p-4">
        <div class="text-sm text-zinc-500 mb-1">本期应缴</div>
        <div class="text-2xl font-bold text-amber-600">
          ¥{{ summaries.reduce((s, i) => s + Number(i.total_tax_amount || 0), 0).toLocaleString() }}
        </div>
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4">
        <div class="text-sm text-zinc-500 mb-1">本期已缴</div>
        <div class="text-2xl font-bold text-green-600">
          ¥{{ summaries.reduce((s, i) => s + Number(i.total_paid_amount || 0), 0).toLocaleString() }}
        </div>
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4">
        <div class="text-sm text-zinc-500 mb-1">本期未缴</div>
        <div class="text-2xl font-bold text-red-600">
          ¥{{ summaries.reduce((s, i) => s + Number(i.total_unpaid_amount || 0), 0).toLocaleString() }}
        </div>
      </div>
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-stone-50 border-b border-stone-200">
          <tr>
            <th class="text-left px-4 py-3 text-zinc-600 font-medium">税种</th>
            <th class="text-right px-4 py-3 text-zinc-600 font-medium">记录数</th>
            <th class="text-right px-4 py-3 text-zinc-600 font-medium">应缴金额</th>
            <th class="text-right px-4 py-3 text-zinc-600 font-medium">已缴金额</th>
            <th class="text-right px-4 py-3 text-zinc-600 font-medium">未缴金额</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in summaries" :key="s.tax_type" class="border-b border-stone-100">
            <td class="px-4 py-3 font-medium text-zinc-800">{{ s.label }}</td>
            <td class="px-4 py-3 text-right text-zinc-600">{{ s.count }}</td>
            <td class="px-4 py-3 text-right text-amber-600">¥{{ Number(s.total_tax_amount || 0).toLocaleString() }}</td>
            <td class="px-4 py-3 text-right text-green-600">
              ¥{{ Number(s.total_paid_amount || 0).toLocaleString() }}
            </td>
            <td class="px-4 py-3 text-right text-red-600">
              ¥{{ Number(s.total_unpaid_amount || 0).toLocaleString() }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
