<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useI18n } from '@/i18n'

interface IndicatorItem {
  dimension: string
  name: string
  key: string
  unit: string
  value: number | null
  light: string
  green_min?: number
  yellow_min?: number
  green_max?: number
  yellow_max?: number
}

const { t } = useI18n()

const items = ref<IndicatorItem[]>([])
const loading = ref(false)

const LIGHT_LABELS = computed(() => ({
  green: t('finance.indicators_page.greenLight'),
  yellow: t('finance.indicators_page.yellowLight'),
  red: t('finance.indicators_page.redLight'),
  gray: t('finance.indicators_page.noData'),
} as Record<string, string>))
const LIGHT_COLORS: Record<string, string> = {
  green: 'bg-emerald-100 text-emerald-700',
  yellow: 'bg-amber-100 text-amber-700',
  red: 'bg-red-100 text-red-700',
  gray: 'bg-gray-100 text-gray-500',
}

const companyId = localStorage.getItem('companyId') || '1'

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/cockpit/indicators', { params: { company_id: companyId } })
    if (res.data?.items) {
      items.value = res.data.items
    }
  } catch {
    /* empty */
  } finally {
    loading.value = false
  }
})

// Group by dimension
const dimensions = [
  { key: '偿债能力', label: t('finance.indicators_page.solvency') },
  { key: '营运能力', label: t('finance.indicators_page.operations') },
  { key: '盈利能力', label: t('finance.indicators_page.profitability') },
  { key: '成长能力', label: t('finance.indicators_page.growth') },
]

function exportIndicators() {
  const rows = ['维度,指标名称,当前值,单位,绿灯阈值,黄灯阈值,状态']
  for (const item of items.value) {
    rows.push([
      item.dimension, item.name,
      item.value != null ? item.value.toLocaleString() : '-',
      item.unit,
      item.green_min ?? item.green_max ?? '-',
      item.yellow_min ?? item.yellow_max ?? '-',
      LIGHT_LABELS.value[item.light] || item.light,
    ].join(','))
  }
  const blob = new Blob(['﻿' + rows.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = '经营分析指标.csv'; a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="space-y-6">
    <div class="page-header">
      <h2>{{ t('finance.indicators_page.title') }}</h2>
      <button class="px-3 py-1 text-xs bg-stone-500 text-white rounded hover:bg-stone-600" @click="exportIndicators">{{ t('finance.indicators_page.exportCSV') }}</button>
    </div>

    <div v-if="loading" class="text-stone-400 text-xs">{{ t('common.loading') }}</div>

    <div v-for="dim in dimensions" :key="dim.key" class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">{{ dim.label }}</h3>
      <div class="table-compact">
        <table class="data-table text-xs w-auto">
          <thead>
            <tr>
              <th class="w-8">#</th>
              <th class="w-24">指标名称</th>
              <th class="w-20 text-right">数值</th>
              <th class="w-20 text-center">单位</th>
              <th class="w-20 text-center">阈值</th>
              <th class="w-20 text-center">状态</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, idx) in items.filter(i => i.dimension === dim.key)"
              :key="item.key"
              :class="{ 'bg-stone-50': idx % 2 === 0 }"
            >
              <td class="text-stone-400 text-center">{{ idx + 1 }}</td>
              <td class="font-medium">{{ item.name }}</td>
              <td class="text-right font-number">
                {{ item.value !== null ? item.value.toLocaleString() : '—' }}
              </td>
              <td class="text-center text-stone-500">{{ item.unit }}</td>
              <td class="text-center text-stone-500 text-[10px]">
                <template v-if="item.green_min && item.yellow_min">
                  ≥{{ item.green_min }} / ≥{{ item.yellow_min }}
                </template>
                <template v-else-if="item.green_max && item.yellow_max">
                  ≤{{ item.green_max }} / ≤{{ item.yellow_max }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="text-center">
                <span
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="LIGHT_COLORS[item.light]"
                >
                  <span
                    class="w-2 h-2 rounded-full"
                    :class="
                      item.light === 'green'
                        ? 'bg-emerald-500'
                        : item.light === 'yellow'
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                    "
                  ></span>
                  {{ LIGHT_LABELS[item.light] }}
                </span>
              </td>
            </tr>
            <tr v-if="!items.filter(i => i.dimension === dim.key).length">
              <td colspan="6" class="text-center text-stone-400 py-4">{{ t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="form-card bg-stone-50">
      <p class="text-xs text-stone-500">
        阈值说明：{{ t('finance.indicators_page.greenLight') }} = 优于绿线阈值 | {{ t('finance.indicators_page.yellowLight') }} = 介于绿线与红线之间 | {{ t('finance.indicators_page.redLight') }} = 低于红线阈值。 点击指标可查看详细计算过程。
      </p>
    </div>
  </div>
</template>
