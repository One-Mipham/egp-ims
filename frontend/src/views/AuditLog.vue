<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import { listAuditLogs } from '@/api'

const logs = ref<any[]>([])
const loading = ref(false)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

async function load() {
  loading.value = true
  try {
    const res = await listAuditLogs(companyId.value)
    logs.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto max-w-fit min-w-full">
      <DataTable :value="logs" :loading="loading" stripedRows class="shadow-sm" tableStyle="min-width: auto">
        <Column header="时间" style="width:155px">
          <template #body="{ data }">{{ new Date(data.created_at).toLocaleString('zh-CN') }}</template>
        </Column>
        <Column field="user_id" header="操作人ID" style="width:80px" />
        <Column header="操作" style="width:100px">
          <template #body="{ data }">
            <Tag :value="data.action" :severity="data.action.includes('reverse') ? 'danger' : 'info'" />
          </template>
        </Column>
        <Column field="target_type" header="对象类型" style="width:80px" />
        <Column field="target_id" header="对象ID" style="width:70px" />
        <Column field="reason" header="原因" style="width:200px" />
      </DataTable>
    </div>
  </div>
</template>
