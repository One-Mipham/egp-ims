<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import { listPeriods, closePeriod, unclosePeriod } from '@/api'

const periods = ref<any[]>([])
const loading = ref(false)
const showUncloseDialog = ref(false)
const uncloseReason = ref('')
const uncloseTarget = ref('')
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

async function load() {
  loading.value = true
  try {
    const res = await listPeriods(companyId.value)
    periods.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleClose(period: string) {
  try {
    await closePeriod(companyId.value, period)
    await load()
  } catch (e: any) { alert(e.response?.data?.detail) }
}

function handleUnclose(period: string) {
  uncloseTarget.value = period
  uncloseReason.value = ''
  showUncloseDialog.value = true
}

async function confirmUnclose() {
  try {
    await unclosePeriod(companyId.value, uncloseTarget.value, uncloseReason.value)
    showUncloseDialog.value = false
    await load()
  } catch (e: any) { alert(e.response?.data?.detail) }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto max-w-fit min-w-full">
      <DataTable :value="periods" :loading="loading" stripedRows class="shadow-sm" tableStyle="min-width: auto">
        <Column field="period" header="期间" sortable style="width:120px" />
        <Column header="状态" style="width:90px">
          <template #body="{ data }">
            <Tag :value="data.is_closed ? '已结账' : '未结账'" :severity="data.is_closed ? 'success' : 'warning'" />
          </template>
        </Column>
        <Column header="操作" style="width:100px">
        <template #body="{ data }">
          <Button v-if="!data.is_closed" label="结账" text severity="success" size="small" @click="handleClose(data.period)" />
          <Button v-if="data.is_closed" label="反结账" text severity="danger" size="small" @click="handleUnclose(data.period)" />
        </template>
      </Column>
    </DataTable>
    </div>

    <Dialog v-model:visible="showUncloseDialog" header="反结账" :style="{ width: '450px' }" :modal="true">
      <div class="flex flex-col gap-4 py-4">
        <p class="text-sm text-zinc-600 tracking-wide">期间：{{ uncloseTarget }}</p>
        <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">反结账原因（必填）</label>
        <Textarea v-model="uncloseReason" rows="3" class="w-full" placeholder="请输入原因..." />
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showUncloseDialog = false" />
        <Button label="确认反结账" icon="pi pi-exclamation-triangle" severity="danger" @click="confirmUnclose" :disabled="!uncloseReason" />
      </template>
    </Dialog>
  </div>
</template>
