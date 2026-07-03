<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

const indicators = ref([
  { label: '预算完成表现', status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '现金流安全', status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '偿债能力', status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '营运能力', status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '盈利能力', status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '成长能力', status: 'green' as 'green' | 'yellow' | 'red' },
])

const cockpitPaths: Record<string, string> = {
  预算完成表现: '/cockpit/budget',
  现金流安全: '/cockpit/cashflow',
  偿债能力: '/cockpit/indicators',
  营运能力: '/cockpit/indicators',
  盈利能力: '/cockpit/indicators',
  成长能力: '/cockpit/indicators',
}

function goCockpit(label: string) {
  const path = cockpitPaths[label]
  if (path) router.push(path)
}

const loading = ref(false)
const STATUS_CIRCLE_CLASS: Record<string, string> = {
  green: 'circle-green',
  yellow: 'circle-yellow',
  red: 'circle-red',
}
const STATUS_ICON: Record<string, string> = {
  green: 'pi-check-circle',
  yellow: 'pi-exclamation-circle',
  red: 'pi-times-circle',
}
const STATUS_ICON_COLOR: Record<string, string> = {
  green: '#059669',
  yellow: '#d97706',
  red: '#dc2626',
}
const STATUS_LABEL: Record<string, string> = {
  green: '绿灯',
  yellow: '黄灯',
  red: '红灯',
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/cockpit/cockpit-lights')
    if (res.data) {
      for (const ind of indicators.value) {
        if (res.data[ind.label]) ind.status = res.data[ind.label]
      }
    }
  } catch {
    /* use defaults */
  } finally {
    loading.value = false
  }
})

const financeMenu = [
  { label: '公司预算与分析评价', path: '/cockpit/budget', icon: 'pi-chart-line' },
  { label: '现金流计划与融资计划', path: '/cockpit/cashflow', icon: 'pi-money-bill' },
  { label: '公司经营分析指标', path: '/cockpit/indicators', icon: 'pi-chart-bar' },
]
</script>

<template>
  <div class="space-y-6">
    <div class="page-header">
      <h2>财务管理驾驶舱</h2>
    </div>

    <div class="flex flex-col lg:flex-row gap-6">
      <div class="lg:w-56 shrink-0">
        <div class="bg-white border border-stone-200 rounded-sm shadow-sm overflow-hidden">
          <div
            v-for="(item, idx) in financeMenu"
            :key="item.label"
            @click="router.push(item.path)"
            class="px-4 py-2.5 text-sm text-stone-700 hover:bg-stone-50 cursor-pointer transition-colors flex items-center gap-2"
            :class="{ 'border-b border-stone-100': idx < financeMenu.length - 1 }"
          >
            <i :class="['pi', item.icon, 'text-xs']" />
            {{ item.label }}
          </div>
        </div>
      </div>

      <div class="flex-1">
        <div class="flex flex-wrap gap-5 justify-center">
          <div
            v-for="ind in indicators"
            :key="ind.label"
            @click="goCockpit(ind.label)"
            :class="['cockpit-circle', STATUS_CIRCLE_CLASS[ind.status]]"
          >
            <div class="circle-ring" />
            <i
              :class="['pi', STATUS_ICON[ind.status], 'circle-icon']"
              :style="{ color: STATUS_ICON_COLOR[ind.status] }"
            />
            <div class="circle-label">{{ ind.label }}</div>
            <div class="text-[10px] mt-1 font-medium" :style="{ color: STATUS_ICON_COLOR[ind.status] }">
              {{ STATUS_LABEL[ind.status] }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <p class="text-xs text-stone-400 mt-3">点击圆形指示卡可查看详细指标分析</p>
    <p v-if="loading" class="text-stone-400 text-xs tracking-wide">加载数据中...</p>
  </div>
</template>
