<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">自定义账</h2>

    <div class="grid grid-cols-3 gap-4">
      <div class="col-span-1">
        <div class="flex justify-between items-center mb-2">
          <h3 class="font-semibold">已保存查询</h3>
          <span class="text-xs text-gray-500">({{ queries.length }})</span>
        </div>
        <div class="border rounded p-2 space-y-1" style="min-height: 200px">
          <div
            v-for="q in queries"
            :key="q.id"
            class="p-2 rounded cursor-pointer hover:bg-blue-50"
            :class="{ 'bg-blue-100': selectedQuery?.id === q.id }"
            @click="selectQuery(q)"
          >
            <div class="text-sm font-medium">{{ q.name }}</div>
            <div class="text-xs text-gray-500">{{ typeLabel(q.query_type) }}</div>
          </div>
          <div v-if="!queries.length" class="text-center text-gray-400 py-4">暂无保存的查询</div>
        </div>
        <div class="flex gap-2 mt-2">
          <Button label="保存当前" icon="pi pi-save" size="small" @click="openSave" />
          <Button
            label="删除选中"
            icon="pi pi-trash"
            size="small"
            severity="danger"
            :disabled="!selectedQuery"
            @click="confirmDelete"
          />
        </div>
      </div>

      <div class="col-span-2">
        <div class="border rounded p-3 mb-3">
          <div class="flex gap-2 items-end flex-wrap">
            <div>
              <label class="text-xs block mb-1">查询类型</label>
              <Dropdown
                v-model="queryForm.query_type"
                :options="queryTypeOptions"
                optionLabel="label"
                optionValue="value"
                class="w-32"
              />
            </div>
            <div v-if="queryForm.query_type === 'subject'">
              <label class="text-xs block mb-1">{{ t('accounting.gl_page.accountCode') }}</label>
              <InputText v-model="queryForm.filters.account_code" size="small" placeholder="如 660" class="w-32" />
            </div>
            <div v-if="queryForm.query_type === 'aux'">
              <label class="text-xs block mb-1">维度</label>
              <Dropdown
                v-model="queryForm.filters.aux_type"
                :options="auxTypes"
                optionLabel="label"
                optionValue="value"
                size="small"
                class="w-28"
              />
            </div>
            <div v-if="queryForm.query_type === 'aux'">
              <label class="text-xs block mb-1">对象ID</label>
              <InputText
                v-model="queryForm.filters.aux_id_str"
                size="small"
                placeholder="ID"
                class="w-20"
                @update:model-value="queryForm.filters.aux_id = $event ? Number($event) : null"
              />
            </div>
            <div>
              <label class="text-xs block mb-1">{{ t('accounting.gl_page.startPeriod') }}</label>
              <InputText v-model="queryForm.filters.start_period" size="small" placeholder="yyyy-MM" class="w-28" />
            </div>
            <div>
              <label class="text-xs block mb-1">{{ t('accounting.gl_page.endPeriod') }}</label>
              <InputText v-model="queryForm.filters.end_period" size="small" placeholder="yyyy-MM" class="w-28" />
            </div>
            <Button label="执行" icon="pi pi-play" size="small" @click="runQuery" />
          </div>
        </div>

        <DataTable v-if="results.length" :value="results" stripedRows size="small" class="mb-3">
          <Column v-for="col in resultColumns" :key="col.field" :field="col.field" :header="col.header" />
        </DataTable>
        <div v-else-if="ran" class="text-center text-gray-400 py-4">无结果</div>
      </div>
    </div>

    <Dialog v-model:visible="saveVisible" header="保存查询" :modal="true" :style="{ width: '400px' }">
      <div>
        <label class="block text-sm mb-1">查询名称</label>
        <InputText v-model="saveName" class="w-full" />
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="saveVisible = false" />
        <Button :label="t('common.save')" @click="doSave" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from '@/i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import {
  listCustomQueries,
  createCustomQuery,
  deleteCustomQuery,
  executeCustomQuery,
  getSubjectLedger,
  getAuxLedger,
} from '../../api'

const toast = useToast()
const { t } = useI18n()
const companyId = Number(localStorage.getItem('companyId') || '1')
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const queries = ref<any[]>([])
const selectedQuery = ref<any>(null)
const results = ref<any[]>([])
const ran = ref(false)

const queryTypeOptions = [
  { label: '科目账', value: 'subject' },
  { label: '辅助账', value: 'aux' },
  { label: '明细表', value: 'detail' },
]

const auxTypes = [
  { label: '部门', value: 'department' },
  { label: '个人', value: 'person' },
  { label: '往来单位', value: 'counterparty' },
  { label: '项目', value: 'project' },
]

const queryForm = ref({
  query_type: 'subject' as string,
  filters: {
    account_code: '',
    aux_type: 'department',
    aux_id: null as any,
    aux_id_str: '',
    start_period: defaultPeriod,
    end_period: defaultPeriod,
    include_zero: false,
  },
})

const saveVisible = ref(false)
const saveName = ref('')

const resultColumns = computed(() => {
  if (!results.value.length) return []
  return Object.keys(results.value[0]).map(k => ({ field: k, header: k }))
})

function typeLabel(t: string) {
  const m: Record<string, string> = { subject: '科目账', aux: '辅助账', detail: '明细表' }
  return m[t] || t
}

async function loadQueries() {
  const { data } = await listCustomQueries(companyId)
  queries.value = data
}

function selectQuery(q: any) {
  selectedQuery.value = q
  queryForm.value.query_type = q.query_type
  if (q.filters) {
    queryForm.value.filters = { ...queryForm.value.filters, ...q.filters }
  }
  runQuery()
}

async function runQuery() {
  try {
    ran.value = true
    if (selectedQuery.value) {
      const { data } = await executeCustomQuery(
        selectedQuery.value.id,
        companyId,
        queryForm.value.filters.start_period,
        queryForm.value.filters.end_period,
      )
      results.value = Array.isArray(data) ? data : []
    } else if (queryForm.value.query_type === 'subject') {
      const { data } = await getSubjectLedger(
        companyId,
        queryForm.value.filters.start_period,
        queryForm.value.filters.end_period,
        { account_code: queryForm.value.filters.account_code || undefined },
      )
      results.value = data
    } else if (queryForm.value.query_type === 'aux') {
      if (!queryForm.value.filters.aux_id) {
        toast.add({ severity: 'warn', summary: '请输入对象ID', life: 3000 })
        return
      }
      const { data } = await getAuxLedger(
        companyId,
        queryForm.value.filters.aux_type,
        queryForm.value.filters.aux_id,
        queryForm.value.filters.start_period,
        queryForm.value.filters.end_period,
      )
      results.value = data.entries || []
    }
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

function openSave() {
  saveName.value = ''
  saveVisible.value = true
}

async function doSave() {
  await createCustomQuery({
    company_id: companyId,
    name: saveName.value,
    query_type: queryForm.value.query_type,
    filters: queryForm.value.filters,
  })
  toast.add({ severity: 'success', summary: t('common.saveSuccess'), life: 3000 })
  saveVisible.value = false
  await loadQueries()
}

async function confirmDelete() {
  if (!selectedQuery.value) return
  if (!confirm(`确定删除 "${selectedQuery.value.name}" 吗？`)) return
  await deleteCustomQuery(selectedQuery.value.id)
  toast.add({ severity: 'success', summary: t('common.deleteSuccess'), life: 3000 })
  selectedQuery.value = null
  await loadQueries()
}

onMounted(loadQueries)
</script>
