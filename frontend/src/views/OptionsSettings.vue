<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import { lookupCompany, updateCompany } from '@/api'
import { useI18n } from '@/i18n'

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const company = ref<any>({})
const companyId = ref(parseInt(localStorage.getItem('companyId') || '1'))

const form = ref({
  fiscal_year_start: '01-01',
  currency: 'CNY',
  industry: 'consulting',
  internal_control_mode: 'standard',
})

const CONTROL_MODES = [
  { value: 'simplified', label: t('system.simplified'), desc: '制单→记账，无需审核' },
  { value: 'standard', label: t('system.standard'), desc: '制单→审核→记账，标准三岗' },
  { value: 'strict', label: t('system.strict'), desc: '制单→审核→复核→记账，四岗分离' },
]

const INDUSTRIES = [
  { value: 'consulting', label: '咨询/技术服务' },
  { value: 'investment', label: '投资/金融' },
  { value: 'manufacturing', label: '制造业' },
  { value: 'trade', label: '贸易/零售' },
  { value: 'real_estate', label: '房地产' },
  { value: 'other', label: '其他' },
]

const CURRENCIES = [
  { value: 'CNY', label: '人民币 (CNY)' },
  { value: 'USD', label: '美元 (USD)' },
  { value: 'EUR', label: '欧元 (EUR)' },
  { value: 'HKD', label: '港元 (HKD)' },
]

async function load() {
  loading.value = true
  try {
    const res = await lookupCompany(companyId.value)
    company.value = res.data
    form.value = {
      fiscal_year_start: res.data.fiscal_year_start || '01-01',
      currency: res.data.currency || 'CNY',
      industry: res.data.industry || 'consulting',
      internal_control_mode: res.data.internal_control_mode || 'standard',
    }
  } catch {
    // use defaults
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await updateCompany(companyId.value, form.value)
    alert('设置已保存')
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.saveFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="max-w-2xl">
    <h2 class="text-lg font-bold mb-1">{{ t('system.optionsSettings') }}</h2>
    <p class="text-xs text-zinc-400 mb-4">配置业务流程参数与系统偏好</p>

    <div v-if="loading" class="text-sm text-zinc-400">{{ t('common.loading') }}</div>

    <div v-else class="space-y-4">
      <!-- Fiscal year -->
      <div class="bg-white border rounded p-4">
        <h3 class="font-bold text-sm mb-3">{{ t('accounting.periods') }}</h3>
        <div class="flex items-center gap-3">
          <div>
            <label class="text-xs text-zinc-500 block mb-1">{{ t('system.fiscalYearStart') }}</label>
            <input v-model="form.fiscal_year_start" type="text" placeholder="MM-DD" class="border rounded px-2 py-1.5 text-sm w-28" />
          </div>
          <p class="text-xs text-zinc-400">格式 MM-DD（默认为 01-01，即公历年度）</p>
        </div>
      </div>

      <!-- Currency & Industry -->
      <div class="bg-white border rounded p-4">
        <h3 class="font-bold text-sm mb-3">货币与行业</h3>
        <div class="flex gap-6">
          <div>
            <label class="text-xs text-zinc-500 block mb-1">{{ t('system.currency') }}</label>
            <select v-model="form.currency" class="border rounded px-2 py-1.5 text-sm">
              <option v-for="c in CURRENCIES" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500 block mb-1">{{ t('system.industry') }}</label>
            <select v-model="form.industry" class="border rounded px-2 py-1.5 text-sm">
              <option v-for="i in INDUSTRIES" :key="i.value" :value="i.value">{{ i.label }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Internal control -->
      <div class="bg-white border rounded p-4">
        <h3 class="font-bold text-sm mb-3">{{ t('system.internalControlMode') }}</h3>
        <div class="space-y-2">
          <label v-for="m in CONTROL_MODES" :key="m.value" class="flex items-start gap-2 cursor-pointer p-2 rounded hover:bg-stone-50">
            <input type="radio" v-model="form.internal_control_mode" :value="m.value" class="mt-0.5" />
            <div>
              <span class="text-sm font-medium">{{ m.label }}</span>
              <p class="text-xs text-zinc-400">{{ m.desc }}</p>
            </div>
          </label>
        </div>
      </div>

      <Button :label="t('common.save')" icon="pi pi-save" @click="save" :loading="saving" />
    </div>
  </div>
</template>
