<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '@/i18n'
import { getCockpitLights } from '@/api/board'

const { t } = useI18n()
const router = useRouter()

const indicators = ref([
  { label: '证监会/局规定文件', status: 'green' as 'green' | 'yellow' | 'red', path: '/board/filings' },
  { label: '交易所规定文件', status: 'green' as 'green' | 'yellow' | 'red', path: '/board/filings' },
  { label: '股东大会法律文件', status: 'green' as 'green' | 'yellow' | 'red', path: '/board/filings' },
  { label: '财务部门报备文件', status: 'green' as 'green' | 'yellow' | 'red', path: '/board/filings' },
  { label: '内部报批事项', status: 'green' as 'green' | 'yellow' | 'red', path: '/board/approvals' },
  { label: '档案完整度', status: 'green' as 'green' | 'yellow' | 'red', path: '/board/archives' },
])

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

const companyId = parseInt(localStorage.getItem('companyId') || '1')

onMounted(async () => {
  loading.value = true
  try {
    const res = await getCockpitLights(companyId)
    if (res.data?.lights) {
      for (const light of res.data.lights) {
        const ind = indicators.value.find(i => i.label === light.label)
        if (ind) ind.status = light.status
      }
    }
  } catch {
    /* use defaults */
  } finally {
    loading.value = false
  }
})

const quickLinks = [
  { label: '合规报送管理', path: '/board/filings', icon: 'pi-globe' },
  { label: '内部报批流程', path: '/board/approvals', icon: 'pi-send' },
  { label: '三会决议管理', path: '/board/meetings', icon: 'pi-calendar' },
  { label: '股东名册', path: '/board/shareholders', icon: 'pi-users' },
  { label: '档案管理', path: '/board/archives', icon: 'pi-folder' },
  { label: '对接联络日志', path: '/board/contacts', icon: 'pi-phone' },
]
</script>

<template>
  <div class="space-y-6">
    <div class="page-header">
      <h2>{{ t('board.cockpit') }}</h2>
    </div>

    <div class="flex flex-col lg:flex-row gap-6">
      <div class="lg:w-52 shrink-0">
        <div class="bg-white border border-stone-200 rounded-sm shadow-sm overflow-hidden">
          <div
            v-for="(item, idx) in quickLinks"
            :key="item.label"
            @click="router.push(item.path)"
            class="px-4 py-2.5 text-sm text-stone-700 hover:bg-stone-50 cursor-pointer transition-colors flex items-center gap-2"
            :class="{ 'border-b border-stone-100': idx < quickLinks.length - 1 }"
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
            @click="router.push(ind.path)"
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

    <p class="text-xs text-stone-400 mt-3">点击圆形指示卡可查看详细报送/报批/归档记录</p>
    <p v-if="loading" class="text-stone-400 text-xs tracking-wide">{{ t('common.loading') }}</p>
  </div>
</template>
