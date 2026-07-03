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
import { listPositions, listTransactions, createTransaction, updateTransaction, deleteTransaction } from '@/api'

const positions = ref<any[]>([])
const transactions = ref<any[]>([])
const filterPosition = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const showVoucherId = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const TXN_TYPES = [
  { label: '买入', value: 'buy' },
  { label: '卖出', value: 'sell' },
  { label: '资本召唤', value: 'capital_call' },
  { label: '分配返还', value: 'distribution' },
  { label: '分红', value: 'dividend' },
  { label: '利息', value: 'interest' },
]

const TYPE_LABELS: Record<string, string> = {
  buy: '买入',
  sell: '卖出',
  capital_call: '资本召唤',
  distribution: '分配返还',
  dividend: '分红',
  interest: '利息',
}

const emptyForm = () => ({
  position_id: filterPosition.value || null,
  transaction_type: 'buy',
  transaction_date: '',
  quantity: 0,
  price: 0,
  amount: 0,
  fee: 0,
  counterparty_id: null,
  notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [posRes, txnRes] = await Promise.all([
      listPositions(companyId.value),
      listTransactions(companyId.value, filterPosition.value || undefined),
    ])
    positions.value = posRes.data
    transactions.value = txnRes.data
  } finally {
    loading.value = false
  }
}

function getPositionName(posId: number) {
  const pos = positions.value.find((p: any) => p.id === posId)
  return pos ? `${pos.security_name} (${pos.account_code})` : `#${posId}`
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
    transaction_type: row.transaction_type,
    transaction_date: row.transaction_date,
    quantity: row.quantity,
    price: row.price,
    amount: row.amount,
    fee: row.fee,
    counterparty_id: row.counterparty_id,
    notes: row.notes || '',
  }
  isEdit.value = true
  editId.value = row.id
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.position_id || !form.value.transaction_date || !form.value.amount) return
  saving.value = true
  try {
    if (isEdit.value && editId.value) {
      await updateTransaction(editId.value, form.value)
    } else {
      const res = await createTransaction(companyId.value, form.value)
      showVoucherId.value = res.data.voucher_id
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
  if (!confirm('确定删除此交易？关联凭证将一并删除。')) return
  await deleteTransaction(id)
  await load()
}

function onFilterChange() {
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center">
        <h2 class="text-lg font-semibold text-zinc-700">投资交易</h2>
        <Dropdown
          v-model="filterPosition"
          :options="positions"
          optionLabel="security_name"
          optionValue="id"
          placeholder="全部持仓"
          class="w-48"
          @change="onFilterChange"
          showClear
        />
      </div>
      <Button label="新增交易" icon="pi pi-plus" @click="openAdd" />
    </div>

    <div
      v-if="showVoucherId"
      class="mb-3 p-2 bg-green-50 border border-green-200 rounded text-sm flex justify-between items-center"
    >
      <span><i class="pi pi-check-circle text-green-600 mr-1" /> 交易已保存，自动生成凭证 #{{ showVoucherId }}</span>
      <Button icon="pi pi-times" text size="small" @click="showVoucherId = null" />
    </div>

    <DataTable :value="transactions" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="transaction_date" header="日期" sortable style="width: 100px" />
      <Column header="持仓" sortable style="width: 160px">
        <template #body="{ data }">{{ getPositionName(data.position_id) }}</template>
      </Column>
      <Column field="transaction_type" header="类型" sortable style="width: 100px">
        <template #body="{ data }">
          <Tag
            :value="TYPE_LABELS[data.transaction_type] || data.transaction_type"
            :severity="data.transaction_type === 'buy' ? 'info' : data.transaction_type === 'sell' ? 'warn' : 'success'"
          />
        </template>
      </Column>
      <Column field="quantity" header="数量" sortable style="width: 100px">
        <template #body="{ data }">{{ data.quantity.toLocaleString() }}</template>
      </Column>
      <Column field="price" header="价格" sortable style="width: 100px">
        <template #body="{ data }">{{ data.price.toLocaleString() }}</template>
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

    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑交易' : '新增交易（自动生成凭证）'"
      :modal="true"
      class="w-[500px]"
    >
      <div class="flex flex-col gap-3">
        <div>
          <label class="block text-sm mb-1">持仓 *</label
          ><Dropdown
            v-model="form.position_id"
            :options="positions"
            optionLabel="security_name"
            optionValue="id"
            class="w-full"
            filter
            :disabled="isEdit"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">交易类型 *</label
            ><Dropdown
              v-model="form.transaction_type"
              :options="TXN_TYPES"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
          <div>
            <label class="block text-sm mb-1">交易日期 *</label
            ><InputText v-model="form.transaction_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="block text-sm mb-1">数量</label><InputNumber v-model="form.quantity" class="w-full" />
          </div>
          <div><label class="block text-sm mb-1">价格</label><InputNumber v-model="form.price" class="w-full" /></div>
          <div><label class="block text-sm mb-1">手续费</label><InputNumber v-model="form.fee" class="w-full" /></div>
        </div>
        <div><label class="block text-sm mb-1">金额 *</label><InputNumber v-model="form.amount" class="w-full" /></div>
        <div>
          <label class="block text-sm mb-1">备注</label><Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
        <p v-if="!isEdit" class="text-xs text-zinc-400">
          <i class="pi pi-info-circle mr-1" /> 保存后将自动生成会计凭证
        </p>
      </div>
      <template #footer>
        <Button label="取消" text @click="showDialog = false" />
        <Button :label="isEdit ? '更新' : '保存并生成凭证'" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
