<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import {
  listPositions,
  listInvestmentIncome,
  createInvestmentIncome,
  updateInvestmentIncome,
  deleteInvestmentIncome,
} from '@/api'

const positions = ref<any[]>([])
const incomes = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const INCOME_TYPES = [
  { label: '分红', value: 'dividend' },
  { label: '利息', value: 'interest' },
  { label: '已实现收益', value: 'realized_gain' },
  { label: '未实现收益', value: 'unrealized_gain' },
  { label: '其他', value: 'other' },
]
const TYPE_LABELS: Record<string, string> = {
  dividend: '分红',
  interest: '利息',
  realized_gain: '已实现收益',
  unrealized_gain: '未实现收益',
  other: '其他',
}

const emptyForm = () => ({
  position_id: null as number | null,
  income_type: 'dividend',
  income_date: '',
  amount: 0,
  notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [posRes, incRes] = await Promise.all([listPositions(companyId.value), listInvestmentIncome(companyId.value)])
    positions.value = posRes.data
    incomes.value = incRes.data
  } finally {
    loading.value = false
  }
}

function getPositionName(posId: number | null) {
  if (!posId) return '-'
  const pos = positions.value.find((p: any) => p.id === posId)
  return pos ? pos.security_name : `#${posId}`
}

function openAdd() {
  form.value = emptyForm()
  isEdit.value = false
  editId.value = null
  showDialog.value = true
}

function openEdit(row: any) {
  form.value = {
    position_id: row.position_id,
    income_type: row.income_type,
    income_date: row.income_date,
    amount: row.amount,
    notes: row.notes || '',
  }
  isEdit.value = true
  editId.value = row.id
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.income_date || form.value.amount <= 0) return
  saving.value = true
  try {
    if (isEdit.value && editId.value) {
      await updateInvestmentIncome(editId.value, form.value)
    } else {
      await createInvestmentIncome(companyId.value, form.value)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  if (!confirm('确定删除此收益记录？关联凭证将一并删除。')) return
  await deleteInvestmentIncome(id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">投资收益</h2>
      <Button label="新增收益" icon="pi pi-plus" @click="openAdd" />
    </div>

    <DataTable :value="incomes" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="income_date" header="日期" sortable style="width: 100px" />
      <Column header="相关持仓" sortable style="width: 150px">
        <template #body="{ data }">{{ getPositionName(data.position_id) }}</template>
      </Column>
      <Column field="income_type" header="类型" sortable style="width: 120px">
        <template #body="{ data }">
          <Tag
            :value="TYPE_LABELS[data.income_type] || data.income_type"
            :severity="data.income_type === 'dividend' ? 'info' : 'success'"
          />
        </template>
      </Column>
      <Column field="amount" header="金额" sortable style="width: 120px">
        <template #body="{ data }">{{ data.amount.toLocaleString() }}</template>
      </Column>
      <Column field="voucher_id" header="凭证号" sortable style="width: 80px">
        <template #body="{ data }">
          <span v-if="data.voucher_id" class="text-blue-600">#{{ data.voucher_id }}</span>
          <span v-else class="text-zinc-400">-</span>
        </template>
      </Column>
      <Column field="notes" header="备注" />
      <Column header="操作" style="width: 100px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" size="small" severity="secondary" text rounded @click="openEdit(data)" />
            <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑收益' : '新增收益'" :modal="true" class="w-[450px]">
      <div class="flex flex-col gap-3">
        <div>
          <label class="block text-sm mb-1">相关持仓</label
          ><Dropdown
            v-model="form.position_id"
            :options="positions"
            optionLabel="security_name"
            optionValue="id"
            class="w-full"
            showClear
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">收益类型 *</label
            ><Dropdown
              v-model="form.income_type"
              :options="INCOME_TYPES"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
          <div>
            <label class="block text-sm mb-1">日期 *</label
            ><InputText v-model="form.income_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
        </div>
        <div><label class="block text-sm mb-1">金额 *</label><InputNumber v-model="form.amount" class="w-full" /></div>
        <div>
          <label class="block text-sm mb-1">备注</label><Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" text @click="showDialog = false" />
        <Button :label="isEdit ? '更新' : '保存'" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
