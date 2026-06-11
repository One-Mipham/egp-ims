<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'; import Column from 'primevue/column'
import Button from 'primevue/button'; import Dialog from 'primevue/dialog'
import Card from 'primevue/card'; import Tag from 'primevue/tag'
import api from '@/api/index'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const investors = ref<any[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const detailData = ref<any>(null)

async function load() {
  loading.value = true
  try { const r = await api.get('/investments/lp-investors', { params: { company_id: companyId.value } }); investors.value = r.data }
  finally { loading.value = false }
}

async function openDetail(investorId: number) {
  const r = await api.get(`/investments/lp-investors/${investorId}/summary`, { params: { company_id: companyId.value } })
  detailData.value = r.data; detailVisible.value = true
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <h2 class="text-lg font-semibold text-zinc-700 mb-4">LP 投资人管理</h2>

    <DataTable :value="investors" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column header="投资人">
        <template #body="{ data }"><a class="text-indigo-600 hover:underline cursor-pointer" @click="openDetail(data.investor_id)">{{ data.investor_name }}</a></template>
      </Column>
      <Column field="fund_count" header="参与基金数" />
      <Column header="总承诺出资"><template #body="{ data }">¥{{ data.total_committed?.toLocaleString() }}</template></Column>
      <Column header="总实缴"><template #body="{ data }">¥{{ data.total_called?.toLocaleString() }}</template></Column>
      <Column header="实缴率"><template #body="{ data }">{{ data.total_committed ? (data.total_called / data.total_committed * 100).toFixed(1) + '%' : '-' }}</template></Column>
    </DataTable>

    <!-- Investor Detail Dialog -->
    <Dialog v-model:visible="detailVisible" :header="'LP详情: ' + (detailData?.investor_name || '')" :style="{ width: '640px' }" modal>
      <div v-if="detailData" class="space-y-4">
        <div class="grid grid-cols-3 gap-4">
          <Card class="shadow-sm"><template #content><div class="text-xs text-stone-500">参与基金</div><div class="text-lg font-bold">{{ detailData.fund_count }}</div></template></Card>
          <Card class="shadow-sm"><template #content><div class="text-xs text-stone-500">总承诺</div><div class="text-lg font-bold">¥{{ detailData.total_committed?.toLocaleString() }}</div></template></Card>
          <Card class="shadow-sm"><template #content><div class="text-xs text-stone-500">总实缴</div><div class="text-lg font-bold">¥{{ detailData.total_called?.toLocaleString() }}</div></template></Card>
        </div>
        <DataTable :value="detailData.funds" stripedRows size="small">
          <Column field="fund_name" header="基金" />
          <Column header="承诺"><template #body="{ data }">¥{{ data.committed?.toLocaleString() }}</template></Column>
          <Column header="实缴"><template #body="{ data }">¥{{ data.called?.toLocaleString() }}</template></Column>
          <Column header="占比"><template #body="{ data }">{{ data.pct?.toFixed(1) }}%</template></Column>
          <Column header="待缴"><template #body="{ data }">¥{{ data.pending_calls?.toLocaleString() }}</template></Column>
          <Column header="已分配"><template #body="{ data }"><span class="text-emerald-600">¥{{ data.total_distributions?.toLocaleString() }}</span></template></Column>
        </DataTable>
      </div>
    </Dialog>
  </div>
</template>
