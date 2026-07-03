<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Card from 'primevue/card'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import { listCompanies, createCompany } from '@/api'

const companies = ref<any[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const newCompany = ref({
  name: '',
  short_name: '',
  industry: 'consulting',
  internal_control_mode: 'standard',
  currency: 'CNY',
})
const currentCompanyId = computed(() => Number(localStorage.getItem('companyId')))

async function load() {
  loading.value = true
  try {
    const res = await listCompanies()
    companies.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!newCompany.value.name) return
  try {
    const res = await createCompany(newCompany.value)
    localStorage.setItem('companyId', res.data.id)
    showAddDialog.value = false
    newCompany.value = {
      name: '',
      short_name: '',
      industry: 'consulting',
      internal_control_mode: 'standard',
      currency: 'CNY',
    }
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '创建失败')
  }
}

function selectCompany(id: number) {
  localStorage.setItem('companyId', String(id))
  location.reload()
}

onMounted(load)
</script>

<template>
  <div>
    <Card class="shadow-sm mb-6 border border-zinc-200">
      <template #title>当前公司</template>
      <template #content>
        <p class="text-sm text-zinc-500 mb-3 tracking-wide">选择当前操作的公司账套</p>
        <div class="flex gap-2 flex-wrap">
          <Button
            v-for="c in companies"
            :key="c.id"
            :label="c.name"
            :severity="currentCompanyId === c.id ? 'primary' : 'secondary'"
            text
            @click="selectCompany(c.id)"
          />
          <Button label="新增公司" icon="pi pi-plus" text @click="showAddDialog = true" />
        </div>
      </template>
    </Card>

    <!-- Add company dialog -->
    <Dialog v-model:visible="showAddDialog" header="新增公司" :style="{ width: '500px' }">
      <div class="flex flex-col gap-4 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">公司名称 *</label>
          <InputText v-model="newCompany.name" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">简称</label>
          <InputText v-model="newCompany.short_name" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">行业</label>
          <Dropdown
            v-model="newCompany.industry"
            :options="[
              { label: '投资', value: 'investment' },
              { label: '咨询', value: 'consulting' },
              { label: '技术开发', value: 'tech_dev' },
              { label: 'AI', value: 'ai' },
            ]"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">内控模式</label>
          <Dropdown
            v-model="newCompany.internal_control_mode"
            :options="[
              { label: '简化模式', value: 'simplified' },
              { label: '标准模式', value: 'standard' },
              { label: '严格模式', value: 'strict' },
            ]"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <Button label="创建" icon="pi pi-check" @click="handleAdd" />
      </div>
    </Dialog>
  </div>
</template>
