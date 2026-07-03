<script setup lang="ts">
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const summaries = ref([
  { summary: '支付办公费' },
  { summary: '收到销售款' },
  { summary: '计提本月折旧' },
  { summary: '支付员工工资' },
  { summary: '收到银行利息' },
  { summary: '报销差旅费' },
])
</script>

<template>
  <div>
    <div class="bg-white rounded-sm border border-zinc-200 shadow-sm p-6">
      <p class="text-sm text-zinc-500 mb-4">录入凭证时可快速选择的摘要，系统预设</p>
      <DataTable :value="summaries" stripedRows class="shadow-sm" tableStyle="min-width: auto">
        <Column field="summary" header="摘要内容" style="width: 200px" />
      </DataTable>
    </div>
  </div>
</template>
