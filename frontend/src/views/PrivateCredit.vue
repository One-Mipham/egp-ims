<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import api from '@/api/index'
import { listCounterparties } from '@/api'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const items = ref<any[]>([])
const counterparties = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const filterStatus = ref<string | null>(null)

const INST_TYPES = [
  { label: '优先担保 Senior Secured', value: 'senior_secured' },
  { label: '夹层 Mezzanine', value: 'mezzanine' },
  { label: '一揽子 Unitranche', value: 'unitranche' },
  { label: '次级 Subordinated', value: 'subordinated' },
  { label: '过桥 Bridge', value: 'bridge' },
]
const TYPE_LABELS = Object.fromEntries(INST_TYPES.map(t => [t.value, t.label]))
const STATUS_LABELS: Record<string, string> = {
  performing: '正常',
  watchlist: '关注',
  non_performing: '不良',
  restructured: '重组',
  repaid: '已清偿',
}
const RATINGS = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']
const STATUS_FILTERS = [
  { label: '正常', value: 'performing' },
  { label: '关注', value: 'watchlist' },
  { label: '不良', value: 'non_performing' },
  { label: '重组', value: 'restructured' },
  { label: '已清偿', value: 'repaid' },
]

const emptyForm = () => ({
  borrower_name: '',
  instrument_type: 'senior_secured',
  principal_amount: 0,
  interest_rate: 0,
  origination_date: '',
  maturity_date: '',
  outstanding_principal: 0,
  accrued_interest: 0,
  credit_rating: '',
  collateral: '',
  counterparty_id: null as number | null,
})
const form = ref(emptyForm())

// Payment sub-component
const selectedCredit = ref<any>(null)
const showPayDialog = ref(false)
const payForm = ref({ payment_date: '', payment_type: 'interest', amount: 0 })
const payments = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const [cRes, cpRes] = await Promise.all([
      api.get('/investments/private-credit', {
        params: { company_id: companyId.value, ...(filterStatus.value ? { status: filterStatus.value } : {}) },
      }),
      listCounterparties(companyId.value),
    ])
    items.value = cRes.data
    counterparties.value = cpRes.data
  } finally {
    loading.value = false
  }
}

function _getCounterpartyName(id: number | null) {
  if (!id) return '-'
  const cp = counterparties.value.find(c => c.id === id)
  return cp ? cp.name : `#${id}`
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
  if (!form.value.borrower_name) return
  if (isEdit.value && editId.value) {
    await api.put(`/investments/private-credit/${editId.value}`, form.value)
  } else {
    await api.post('/investments/private-credit', form.value, { params: { company_id: companyId.value } })
  }
  showDialog.value = false
  await load()
}
async function handleDelete(id: number) {
  if (!confirm('确定删除？将级联删除还款记录。')) return
  await api.delete(`/investments/private-credit/${id}`)
  await load()
}

// Payments
async function openPayments(row: any) {
  selectedCredit.value = row
  try {
    const r = await api.get(`/investments/private-credit/${row.id}/payments`)
    payments.value = r.data
  } catch {
    payments.value = []
  }
  showPayDialog.value = true
}
async function savePayment() {
  if (!payForm.value.payment_date || !payForm.value.amount) return
  await api.post(`/investments/private-credit/${selectedCredit.value.id}/payments`, payForm.value, {
    params: { company_id: companyId.value },
  })
  try {
    const r = await api.get(`/investments/private-credit/${selectedCredit.value.id}/payments`)
    payments.value = r.data
  } catch {}
  payForm.value = { payment_date: '', payment_type: 'interest', amount: 0 }
}
async function deletePayment(payId: number) {
  if (!confirm('确定删除？关联凭证将一并删除。')) return
  await api.delete(`/investments/private-credit/${selectedCredit.value.id}/payments/${payId}`)
  try {
    const r = await api.get(`/investments/private-credit/${selectedCredit.value.id}/payments`)
    payments.value = r.data
  } catch {}
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">私募信贷资产</h2>
      <Button label="新增信贷" icon="pi pi-plus" size="small" @click="openAdd" />
    </div>

    <div class="flex gap-3 mb-3">
      <Dropdown
        v-model="filterStatus"
        :options="STATUS_FILTERS"
        optionLabel="label"
        optionValue="value"
        placeholder="全部状态"
        showClear
        class="w-36"
        @change="load"
      />
    </div>

    <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="borrower_name" header="借款人" sortable />
      <Column header="类型"
        ><template #body="{ data }"
          ><Tag :value="TYPE_LABELS[data.instrument_type] || data.instrument_type" severity="info" /></template
      ></Column>
      <Column header="本金"
        ><template #body="{ data }">¥{{ data.principal_amount?.toLocaleString() }}</template></Column
      >
      <Column header="利率"
        ><template #body="{ data }">{{ data.interest_rate }}%</template></Column
      >
      <Column header="未偿本金"
        ><template #body="{ data }">¥{{ data.outstanding_principal?.toLocaleString() }}</template></Column
      >
      <Column field="maturity_date" header="到期日" />
      <Column header="评级"
        ><template #body="{ data }"
          ><Tag
            v-if="data.credit_rating"
            :value="data.credit_rating"
            :severity="
              ['AAA', 'AA', 'A'].includes(data.credit_rating)
                ? 'success'
                : ['BBB', 'BB'].includes(data.credit_rating)
                  ? 'warn'
                  : 'danger'
            " /></template
      ></Column>
      <Column header="状态"
        ><template #body="{ data }"
          ><Tag
            :value="STATUS_LABELS[data.status] || data.status"
            :severity="
              data.status === 'performing'
                ? 'success'
                : data.status === 'watchlist'
                  ? 'warn'
                  : data.status === 'repaid'
                    ? 'info'
                    : 'danger'
            " /></template
      ></Column>
      <Column header="操作" style="width: 140px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button
              icon="pi pi-dollar"
              size="small"
              severity="info"
              text
              rounded
              @click="openPayments(data)"
              title="还款记录"
            />
            <Button icon="pi pi-pencil" size="small" severity="secondary" text rounded @click="openEdit(data)" />
            <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Credit Dialog -->
    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑信贷' : '新增信贷'" :style="{ width: '520px' }" modal>
      <div class="flex flex-col gap-3 pt-2">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">借款人 *</label
            ><InputText v-model="form.borrower_name" class="w-full" />
          </div>
          <div>
            <label class="text-sm text-stone-600">类型</label
            ><Dropdown
              v-model="form.instrument_type"
              :options="INST_TYPES"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">本金</label
            ><InputNumber v-model="form.principal_amount" mode="currency" currency="CNY" class="w-full" />
          </div>
          <div>
            <label class="text-sm text-stone-600">年利率%</label
            ><InputNumber v-model="form.interest_rate" suffix="%" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">起始日</label
            ><InputText v-model="form.origination_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
          <div>
            <label class="text-sm text-stone-600">到期日</label
            ><InputText v-model="form.maturity_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="text-sm text-stone-600">未偿本金</label
            ><InputNumber v-model="form.outstanding_principal" mode="currency" currency="CNY" class="w-full" />
          </div>
          <div>
            <label class="text-sm text-stone-600">应计利息</label
            ><InputNumber v-model="form.accrued_interest" mode="currency" currency="CNY" class="w-full" />
          </div>
          <div>
            <label class="text-sm text-stone-600">评级</label
            ><Dropdown v-model="form.credit_rating" :options="RATINGS" class="w-full" />
          </div>
        </div>
        <div>
          <label class="text-sm text-stone-600">担保/抵押品</label
          ><InputText v-model="form.collateral" class="w-full" />
        </div>
        <div>
          <label class="text-sm text-stone-600">关联单位</label
          ><Dropdown
            v-model="form.counterparty_id"
            :options="counterparties"
            optionLabel="name"
            optionValue="id"
            class="w-full"
            showClear
            filter
          />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showDialog = false" /><Button
          label="保存"
          @click="handleSave"
          :disabled="!form.borrower_name"
      /></template>
    </Dialog>

    <!-- Payments Dialog -->
    <Dialog
      v-model:visible="showPayDialog"
      :header="'还款记录: ' + (selectedCredit?.borrower_name || '')"
      :style="{ width: '600px' }"
      modal
    >
      <div class="flex gap-2 mb-3 items-end">
        <div>
          <label class="text-xs text-stone-400 block">日期</label
          ><InputText v-model="payForm.payment_date" class="w-28" placeholder="YYYY-MM-DD" />
        </div>
        <div>
          <label class="text-xs text-stone-400 block">类型</label
          ><Dropdown
            v-model="payForm.payment_type"
            :options="[
              { label: '利息', value: 'interest' },
              { label: '本金', value: 'principal' },
              { label: '费用', value: 'fee' },
            ]"
            optionLabel="label"
            optionValue="value"
            class="w-24"
          />
        </div>
        <div>
          <label class="text-xs text-stone-400 block">金额</label
          ><InputNumber v-model="payForm.amount" mode="currency" currency="CNY" class="w-36" />
        </div>
        <Button
          icon="pi pi-plus"
          size="small"
          @click="savePayment"
          :disabled="!payForm.payment_date || !payForm.amount"
        />
      </div>
      <DataTable :value="payments" stripedRows size="small">
        <Column field="payment_date" header="日期" />
        <Column header="类型"
          ><template #body="{ data }"
            ><Tag
              :value="data.payment_type === 'interest' ? '利息' : data.payment_type === 'principal' ? '本金' : '费用'"
              :severity="
                data.payment_type === 'interest' ? 'info' : data.payment_type === 'principal' ? 'success' : 'warn'
              " /></template
        ></Column>
        <Column header="金额"
          ><template #body="{ data }">¥{{ data.amount?.toLocaleString() }}</template></Column
        >
        <Column header="凭证"
          ><template #body="{ data }"
            ><span v-if="data.voucher_id" class="text-blue-600">#{{ data.voucher_id }}</span
            ><span v-else class="text-stone-300">-</span></template
          ></Column
        >
        <Column header="" style="width: 50px"
          ><template #body="{ data }"
            ><Button
              icon="pi pi-trash"
              size="small"
              severity="danger"
              text
              rounded
              @click="deletePayment(data.id)" /></template
        ></Column>
      </DataTable>
    </Dialog>
  </div>
</template>
