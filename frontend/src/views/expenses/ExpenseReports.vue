<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { expenseStats, listExpenseReports } from '@/api/expenses'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'

const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const reports = ref<any[]>([])
const stats = ref<any>(null)
const loading = ref(false)

const filters = ref({ start_date: '', end_date: '' })

const statusLabels: Record<string, string> = {
  draft: '草稿', submitted: '待审批', dept_approved: '部门已批',
  finance_approved: '财务已批', director_approved: '总监已批',
  unit_head_approved: '已审批', paid: '已付款', closed: '已归档', rejected: '已驳回',
}

const fetchAll = async () => {
  loading.value = true
  try {
    const [rRes, sRes] = await Promise.all([
      listExpenseReports(companyId),
      expenseStats(companyId, filters.value.start_date || undefined, filters.value.end_date || undefined),
    ])
    reports.value = rRes.data
    stats.value = sRes.data
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e.message, life: 3000 })
  } finally { loading.value = false }
}

onMounted(fetchAll)
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1 class="text-xl font-bold mb-4">7.6 查询统计</h1>

    <!-- Summary cards -->
    <div v-if="stats" class="grid grid-cols-3 gap-4 mb-6">
      <div class="bg-white rounded-sm border border-stone-200 p-4 shadow-sm">
        <div class="text-sm text-gray-500">报销单数</div>
        <div class="text-2xl font-bold">{{ stats.total_count }}</div>
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4 shadow-sm">
        <div class="text-sm text-gray-500">报销总额</div>
        <div class="text-2xl font-bold">¥{{ stats.total_amount?.toLocaleString() }}</div>
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4 shadow-sm">
        <div class="text-sm text-gray-500 mb-2">日期筛选</div>
        <div class="flex gap-2 items-center">
          <InputText type="date" v-model="filters.start_date" class="w-32" />
          <span class="text-gray-400">-</span>
          <InputText type="date" v-model="filters.end_date" class="w-32" />
          <Button icon="pi pi-search" size="small" @click="fetchAll" />
        </div>
      </div>
    </div>

    <!-- By status -->
    <div v-if="stats?.by_status?.length" class="mb-6">
      <h2 class="text-lg font-semibold mb-2">按状态汇总</h2>
      <div class="flex gap-3 flex-wrap">
        <div v-for="s in stats.by_status" :key="s.status" class="bg-gray-50 border rounded px-3 py-2 text-sm">
          <span class="font-medium">{{ statusLabels[s.status] || s.status }}</span>
          <span class="text-gray-500 ml-2">¥{{ s.amount?.toLocaleString() }}</span>
        </div>
      </div>
    </div>

    <!-- Reports table -->
    <DataTable :value="reports" :loading="loading" stripedRows size="small" class="text-sm">
      <Column field="report_no" header="单号" class="font-mono" />
      <Column header="申请人">
        <template #body="slotProps">{{ slotProps.data.applicant_id }}</template>
      </Column>
      <Column field="expense_date" header="费用日期" />
      <Column header="金额">
        <template #body="slotProps">¥{{ slotProps.data.total_amount?.toLocaleString() }}</template>
      </Column>
      <Column header="状态">
        <template #body="slotProps">{{ statusLabels[slotProps.data.status] || slotProps.data.status }}</template>
      </Column>
      <Column field="created_at" header="创建时间" />
    </DataTable>
  </div>
</template>
