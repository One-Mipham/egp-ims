<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import { listFunds, createFund, updateFund, deleteFund } from '@/api'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const FUND_TYPES = [
  { label: '私募股权基金', value: 'private_fund' },
  { label: '对冲基金', value: 'hedge_fund' },
  { label: 'FOF', value: 'fof' },
  { label: '信托计划', value: 'trust_plan' },
]
const TYPE_LABELS: Record<string, string> = Object.fromEntries(FUND_TYPES.map(t => [t.value, t.label]))
const STATUS_LABELS: Record<string, string> = {
  raising: '募资中',
  active: '运营中',
  liquidating: '清算中',
  liquidated: '已清算',
}

const emptyForm = () => ({
  fund_name: '',
  fund_type: 'private_fund',
  management_company: '',
  inception_date: '',
  currency: 'CNY',
  total_commitment: 0,
  portfolio_id: null as number | null,
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const res = await listFunds(companyId.value)
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
  if (!form.value.fund_name) return
  if (isEdit.value && editId.value) {
    await updateFund(editId.value, form.value)
  } else {
    await createFund(companyId.value, form.value)
  }
  showDialog.value = false
  await load()
}
async function handleDelete(id: number) {
  if (!confirm('确定删除此基金？将级联删除资本账户/召唤/分配记录。')) return
  await deleteFund(id)
  await load()
}
function goDetail(id: number) {
  router.push(`/finance/investments/funds/${id}`)
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">基金管理</h2>
      <Button label="新增基金" icon="pi pi-plus" size="small" @click="openAdd" />
    </div>

    <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="fund_name" header="基金名称" sortable>
        <template #body="{ data }"
          ><a class="text-indigo-600 hover:underline cursor-pointer" @click="goDetail(data.id)">{{
            data.fund_name
          }}</a></template
        >
      </Column>
      <Column header="类型"
        ><template #body="{ data }"
          ><Tag :value="TYPE_LABELS[data.fund_type] || data.fund_type" severity="info" class="text-xs" /></template
      ></Column>
      <Column field="management_company" header="管理公司" />
      <Column field="currency" header="币种" />
      <Column header="总规模"
        ><template #body="{ data }">{{ data.total_commitment?.toLocaleString() }}</template></Column
      >
      <Column header="状态"
        ><template #body="{ data }"
          ><Tag
            :value="STATUS_LABELS[data.status] || data.status"
            :severity="
              data.status === 'active' ? 'success' : data.status === 'raising' ? 'warn' : 'danger'
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

    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑基金' : '新增基金'" :style="{ width: '480px' }" modal>
      <div class="flex flex-col gap-3 pt-2">
        <div>
          <label class="text-sm text-stone-600">基金名称 *</label><InputText v-model="form.fund_name" class="w-full" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">类型</label
            ><Dropdown
              v-model="form.fund_type"
              :options="FUND_TYPES"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-sm text-stone-600">币种</label
            ><Dropdown v-model="form.currency" :options="['CNY', 'USD', 'HKD']" class="w-full" />
          </div>
        </div>
        <div>
          <label class="text-sm text-stone-600">管理公司</label
          ><InputText v-model="form.management_company" class="w-full" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">成立日期</label
            ><InputText v-model="form.inception_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
          <div>
            <label class="text-sm text-stone-600">总规模</label
            ><InputNumber v-model="form.total_commitment" mode="currency" currency="CNY" class="w-full" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="showDialog = false" />
        <Button label="保存" @click="handleSave" :disabled="!form.fund_name" />
      </template>
    </Dialog>
  </div>
</template>
