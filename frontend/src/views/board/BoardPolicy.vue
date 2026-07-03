<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import { type BoardFilingData, listFilings, upsertFiling } from '@/api/board'

interface PolicyTab {
  label: string
  title: string
  docSubtype: string
}

const tabs: PolicyTab[] = [
  { label: '董事会工作条例', title: '董事会工作条例', docSubtype: 'bylaws' },
  { label: '提名委员会', title: '提名委员会工作细则', docSubtype: 'nomination' },
  { label: '薪酬与绩效考核委员会', title: '薪酬与绩效考核委员会工作细则', docSubtype: 'compensation' },
  { label: '战略发展委员会', title: '战略发展委员会工作细则', docSubtype: 'strategy' },
  { label: '审计与稽核委员会', title: '审计与稽核委员会工作细则', docSubtype: 'audit' },
  { label: '董秘工作职责', title: '董事会秘书工作职责', docSubtype: 'secretary' },
]

const activeTab = ref(0)
const policyContent = ref('')
const policyTitle = ref('')
const saving = ref(false)
const loading = ref(false)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

function switchTab(idx: number) {
  activeTab.value = idx
  policyTitle.value = tabs[idx].title
  loadPolicy()
}

async function loadPolicy() {
  loading.value = true
  try {
    const res = await listFilings(companyId.value, 'policy', tabs[activeTab.value].docSubtype)
    if (res.data && res.data.length > 0) {
      policyContent.value = res.data[0].content || ''
      policyTitle.value = res.data[0].title || tabs[activeTab.value].title
    } else {
      policyContent.value = ''
      policyTitle.value = tabs[activeTab.value].title
    }
  } catch {
    /* */
  } finally {
    loading.value = false
  }
}

async function savePolicy() {
  saving.value = true
  try {
    await upsertFiling({
      company_id: companyId.value,
      doc_type: 'policy',
      doc_subtype: tabs[activeTab.value].docSubtype,
      title: policyTitle.value,
      content: policyContent.value,
    })
  } catch (e: any) {
    alert(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  policyTitle.value = tabs[0].title
  loadPolicy()
})
</script>

<template>
  <div class="space-y-6">
    <div class="page-header"><h2>董事会工作制度与职责</h2></div>

    <!-- Tabs -->
    <div class="flex flex-wrap gap-1 border-b border-stone-200">
      <button
        v-for="(tab, idx) in tabs"
        :key="idx"
        @click="switchTab(idx)"
        class="px-3 py-2 text-xs font-medium transition-colors border-b-2"
        :class="
          activeTab === idx
            ? 'text-amber-700 border-amber-500 bg-amber-50'
            : 'text-stone-500 border-transparent hover:text-stone-700 hover:border-stone-300'
        "
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="form-card">
      <div class="flex items-center justify-between mb-3">
        <InputText v-model="policyTitle" class="text-sm font-semibold w-96" />
        <Button label="保存文档" icon="pi pi-check" size="small" @click="savePolicy" :loading="saving" />
      </div>
      <Textarea
        v-model="policyContent"
        rows="16"
        class="w-full text-sm font-mono"
        placeholder="在此编写文档内容..."
        :disabled="loading"
      />
    </div>
  </div>
</template>
