<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import { listSecurities, createSecurity, updateSecurity, deleteSecurity } from '@/api'

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const filterType = ref<string | null>(null)
const filterExchange = ref<string | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const SEC_TYPES = [
  { label: '股票 Equity', value: 'equity' },
  { label: '债券 Bond', value: 'bond' },
  { label: '基金 Fund', value: 'fund' },
  { label: 'ETF', value: 'etf' },
  { label: '衍生品 Derivative', value: 'derivative' },
  { label: '大宗商品 Commodity', value: 'commodity' },
  { label: '外汇 Forex', value: 'forex' },
]
const EXCHANGES = [
  { label: '上交所 SSE', value: 'SSE' },
  { label: '深交所 SZSE', value: 'SZSE' },
  { label: '港交所 SEHK', value: 'SEHK' },
  { label: '纽交所 NYSE', value: 'NYSE' },
  { label: '纳斯达克 NASDAQ', value: 'NASDAQ' },
]
const TYPE_LABELS: Record<string, string> = Object.fromEntries(SEC_TYPES.map(t => [t.value, t.label]))
const EXCH_LABELS: Record<string, string> = Object.fromEntries(EXCHANGES.map(e => [e.value, e.label]))

const emptyForm = () => ({
  security_code: '',
  security_name: '',
  security_type: 'equity',
  exchange: '',
  currency: 'CNY',
  isin_code: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const res = await listSecurities(companyId.value, filterType.value || undefined, filterExchange.value || undefined)
    items.value = res.data
  } finally {
    loading.value = false
  }
}

function openAdd() {
  form.value = emptyForm()
  isEdit.value = false
  editId.value = null
  showDialog.value = true
}
function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true
  editId.value = row.id
  showDialog.value = true
}
async function handleSave() {
  if (!form.value.security_code || !form.value.security_name) return
  if (isEdit.value && editId.value) {
    await updateSecurity(editId.value, form.value)
  } else {
    await createSecurity(companyId.value, form.value)
  }
  showDialog.value = false
  await load()
}
async function handleDelete(id: number) {
  if (!confirm('确定删除？')) return
  await deleteSecurity(id)
  await load()
}
function onFilterChange() {
  load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">证券主数据</h2>
      <Button label="新增证券" icon="pi pi-plus" size="small" @click="openAdd" />
    </div>

    <div class="flex gap-3 mb-3">
      <Dropdown
        v-model="filterType"
        :options="SEC_TYPES"
        optionLabel="label"
        optionValue="value"
        placeholder="全部类型"
        showClear
        class="w-48"
        @change="onFilterChange"
      />
      <Dropdown
        v-model="filterExchange"
        :options="EXCHANGES"
        optionLabel="label"
        optionValue="value"
        placeholder="全部交易所"
        showClear
        class="w-48"
        @change="onFilterChange"
      />
    </div>

    <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
      <Column field="security_code" header="代码" sortable />
      <Column field="security_name" header="名称" sortable />
      <Column header="类型" sortable
        ><template #body="{ data }"
          ><Tag
            :value="TYPE_LABELS[data.security_type] || data.security_type"
            severity="info"
            class="text-xs" /></template
      ></Column>
      <Column header="交易所"
        ><template #body="{ data }">{{ EXCH_LABELS[data.exchange] || data.exchange || '-' }}</template></Column
      >
      <Column field="currency" header="币种" />
      <Column field="isin_code" header="ISIN" />
      <Column header="状态"
        ><template #body="{ data }"
          ><Tag
            :value="data.status === 'active' ? '活跃' : data.status === 'inactive' ? '停用' : '已退市'"
            :severity="
              data.status === 'active' ? 'success' : data.status === 'inactive' ? 'warn' : 'danger'
            " /></template
      ></Column>
      <Column header="操作" style="width: 100px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" size="small" severity="secondary" text rounded @click="openEdit(data)" />
            <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑证券' : '新增证券'" :style="{ width: '480px' }" modal>
      <div class="flex flex-col gap-3 pt-2">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">代码 *</label
            ><InputText v-model="form.security_code" class="w-full" placeholder="如 00700.HK" />
          </div>
          <div>
            <label class="text-sm text-stone-600">名称 *</label
            ><InputText v-model="form.security_name" class="w-full" placeholder="如 腾讯控股" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">类型</label
            ><Dropdown
              v-model="form.security_type"
              :options="SEC_TYPES"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-sm text-stone-600">交易所</label
            ><Dropdown
              v-model="form.exchange"
              :options="EXCHANGES"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              showClear
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">币种</label
            ><Dropdown v-model="form.currency" :options="['CNY', 'USD', 'HKD', 'EUR', 'JPY']" class="w-full" />
          </div>
          <div>
            <label class="text-sm text-stone-600">ISIN</label><InputText v-model="form.isin_code" class="w-full" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showDialog = false" />
        <Button label="保存" @click="handleSave" :disabled="!form.security_code || !form.security_name" />
      </template>
    </Dialog>
  </div>
</template>
