<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '@/i18n'
import api from '@/api'

const router = useRouter()
const { t } = useI18n()

type LightStatus = 'green' | 'yellow' | 'red' | 'gray'

const indicators = ref([
  { label: '预算完成表现', status: 'gray' as LightStatus },
  { label: '现金流安全', status: 'gray' as LightStatus },
  { label: '偿债能力', status: 'gray' as LightStatus },
  { label: '营运能力', status: 'gray' as LightStatus },
  { label: '盈利能力', status: 'gray' as LightStatus },
  { label: '成长能力', status: 'gray' as LightStatus },
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
  gray: 'circle-gray',
}
const STATUS_ICON: Record<string, string> = {
  green: 'pi-check-circle',
  yellow: 'pi-exclamation-circle',
  red: 'pi-times-circle',
  gray: 'pi-minus-circle',
}
const STATUS_ICON_COLOR: Record<string, string> = {
  green: '#059669',
  yellow: '#d97706',
  red: '#dc2626',
  gray: '#9ca3af',
}
const STATUS_LABEL = computed(() => ({
  green: t('finance.indicators_page.greenLight'),
  yellow: t('finance.indicators_page.yellowLight'),
  red: t('finance.indicators_page.redLight'),
  gray: t('finance.indicators_page.noData'),
}))

const companyId = localStorage.getItem('companyId') || '1'

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/cockpit/cockpit-lights', { params: { company_id: companyId } })
    if (res.data) {
      for (const ind of indicators.value) {
        if (res.data[ind.label]) ind.status = res.data[ind.label]
      }
    }
  } catch {
    /* use defaults (gray) */
  } finally {
    loading.value = false
  }
})

const financeMenu = [
  { label: t('finance.budget'), path: '/cockpit/budget', icon: 'pi-chart-line' },
  { label: t('finance.cashflow'), path: '/cockpit/cashflow', icon: 'pi-money-bill' },
  { label: t('finance.indicators'), path: '/cockpit/indicators', icon: 'pi-chart-bar' },
]
</script>

<template>
  <div class="space-y-6">
    <div class="page-header">
      <h2>{{ t('finance.cockpit') }}</h2>
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
    <p v-if="loading" class="text-stone-400 text-xs tracking-wide">{{ t('common.loading') }}</p>
  </div>
</template>
