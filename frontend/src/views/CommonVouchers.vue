<script setup lang="ts">
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const vouchers = ref<any[]>([
  { code: 'CV001', name: '计提工资', entries: '借：管理费用 贷：应付职工薪酬' },
  { code: 'CV002', name: '计提折旧', entries: '借：管理费用 贷：累计折旧' },
])
</script>

<template>
  <div>
    <div class="bg-white rounded-sm border border-zinc-200 shadow-sm p-6">
      <p class="text-sm text-zinc-500 mb-4">预置的常用会计分录模板，创建凭证时可选用</p>
      <DataTable :value="vouchers" stripedRows class="shadow-sm" tableStyle="min-width: auto">
        <Column field="code" :header="t('common.code')" style="width: 80px" />
        <Column field="name" :header="t('accounting.vouchers_page.summary')" style="width: 120px" />
        <Column field="entries" header="分录内容" style="width: 320px" />
      </DataTable>
    </div>
  </div>
</template>
