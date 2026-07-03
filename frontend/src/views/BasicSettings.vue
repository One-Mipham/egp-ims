<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listCompanies, updateCompany } from '@/api'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'

const companyForm = ref({
  name: '',
  short_name: '',
  english_name: '',
  english_short_name: '',
  industry: '',
  tax_number: '',
  tax_region: '',
  website: '',
  email: '',
  address: '',
  phone: '',
  contact_person: '',
  currency: 'CNY',
  fiscal_year_start: '01-01',
  internal_control_mode: 'standard',
})

const loading = ref(false)
const saving = ref(false)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const INDUSTRY_OPTIONS = [
  { label: '信息技术', value: 'IT' },
  { label: '制造业', value: 'manufacturing' },
  { label: '金融业', value: 'finance' },
  { label: '咨询业', value: 'consulting' },
  { label: '贸易', value: 'trade' },
  { label: '其他', value: 'other' },
]
const IC_OPTIONS = [
  { label: '简化模式', value: 'simplified' },
  { label: '标准模式', value: 'standard' },
  { label: '严格模式', value: 'strict' },
]

async function load() {
  loading.value = true
  try {
    const res = await listCompanies()
    const company = res.data.find((c: any) => c.id === companyId.value)
    if (company) {
      companyForm.value = {
        name: company.name || '',
        short_name: company.short_name || '',
        english_name: company.english_name || '',
        english_short_name: company.english_short_name || '',
        industry: company.industry || '',
        tax_number: company.tax_number || '',
        tax_region: company.tax_region || '',
        website: company.website || '',
        email: company.email || '',
        address: company.address || '',
        phone: company.phone || '',
        contact_person: company.contact_person || '',
        currency: company.currency || 'CNY',
        fiscal_year_start: company.fiscal_year_start || '01-01',
        internal_control_mode: company.internal_control_mode || 'standard',
      }
    }
  } catch {
    alert('加载公司信息失败')
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await updateCompany(companyId.value, companyForm.value)
    alert('保存成功')
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="loading" class="text-zinc-400">加载中...</div>
    <div v-else class="bg-white rounded-sm border border-zinc-200 shadow-sm p-6 max-w-2xl">
      <div class="flex flex-col gap-5">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">公司名称</label>
            <InputText v-model="companyForm.name" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">公司简称</label>
            <InputText v-model="companyForm.short_name" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">公司英文名称</label>
            <InputText v-model="companyForm.english_name" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">英文简称</label>
            <InputText v-model="companyForm.english_short_name" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">所属行业</label>
            <Dropdown
              v-model="companyForm.industry"
              :options="INDUSTRY_OPTIONS"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              placeholder="选择行业"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">内控模式</label>
            <Dropdown
              v-model="companyForm.internal_control_mode"
              :options="IC_OPTIONS"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税号</label>
            <InputText v-model="companyForm.tax_number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">报税区域</label>
            <InputText v-model="companyForm.tax_region" class="w-full" placeholder="如：青岛市市南区" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">公司网站</label>
            <InputText v-model="companyForm.website" class="w-full" placeholder="https://" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">公司邮箱</label>
            <InputText v-model="companyForm.email" class="w-full" type="email" placeholder="company@example.com" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">公司电话</label>
            <InputText v-model="companyForm.phone" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">联系人</label>
            <InputText v-model="companyForm.contact_person" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">地址</label>
          <Textarea v-model="companyForm.address" rows="2" class="w-full" />
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">币种</label>
            <InputText v-model="companyForm.currency" class="w-full" disabled />
          </div>
          <div class="flex-1"></div>
        </div>
        <div class="flex gap-2 pt-2">
          <Button label="保存" icon="pi pi-check" @click="save" :loading="saving" />
          <Button label="重置" icon="pi pi-refresh" text @click="load" />
        </div>
      </div>
    </div>
  </div>
</template>
