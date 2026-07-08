<script setup lang="ts">
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const types = ref([
  { code: '收', name: '收款凭证', prefix: '收' },
  { code: '付', name: '付款凭证', prefix: '付' },
  { code: '转', name: '转账凭证', prefix: '转' },
])
</script>

<template>
  <div>
    <div class="bg-white rounded-sm border border-zinc-200 shadow-sm p-6">
      <p class="text-sm text-zinc-500 mb-4">系统预设凭证类别，不可增删</p>
      <DataTable :value="types" stripedRows class="shadow-sm" tableStyle="min-width: auto">
        <Column field="code" header="类别代码" style="width: 80px" />
        <Column field="name" :header="t('common.name')" style="width: 140px" />
        <Column field="prefix" header="编号前缀" style="width: 80px" />
      </DataTable>
    </div>
  </div>
</template>
