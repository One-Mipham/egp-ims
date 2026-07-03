<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import Card from 'primevue/card'
import {
  listFunds,
  listCapitalAccounts,
  createCapitalAccount,
  updateCapitalAccount,
  deleteCapitalAccount,
  listCapitalCalls,
  createCapitalCall,
  deleteCapitalCall,
  listFundDistributions,
  createFundDistribution,
  deleteFundDistribution,
  listCounterparties,
} from '@/api'

const route = useRoute()
const router = useRouter()
const fundId = computed(() => parseInt(route.params.fundId as string))
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const fund = ref<any>(null)
const accounts = ref<any[]>([])
const calls = ref<any[]>([])
const distributions = ref<any[]>([])
const counterparties = ref<any[]>([])
const loading = ref(false)

// Capital Account dialog
const showAcctDialog = ref(false)
const isEditAcct = ref(false)
const editAcctId = ref<number | null>(null)
const acctForm = ref({ investor_id: null as number | null, committed_capital: 0, called_capital: 0, ownership_pct: 0 })

// Capital Call dialog
const showCallDialog = ref(false)
const callForm = ref({ call_date: '', call_amount: 0, due_date: '', notes: '' })

// Distribution dialog
const showDistDialog = ref(false)
const distForm = ref({ distribution_date: '', amount: 0, distribution_type: 'income', notes: '' })

const DIST_TYPES = [
  { label: '收益分配', value: 'income' },
  { label: '返还本金', value: 'return_of_capital' },
  { label: 'Carry分配', value: 'carry' },
]

function getInvestorName(id: number) {
  const cp = counterparties.value.find(c => c.id === id)
  return cp ? cp.name : `#${id}`
}

async function loadAll() {
  loading.value = true
  try {
    const [fRes, aRes, cRes, dRes, cpRes] = await Promise.all([
      listFunds(companyId.value),
      listCapitalAccounts(fundId.value),
      listCapitalCalls(fundId.value),
      listFundDistributions(fundId.value),
      listCounterparties(companyId.value),
    ])
    fund.value = fRes.data.find((f: any) => f.id === fundId.value)
    accounts.value = aRes.data
    calls.value = cRes.data
    distributions.value = dRes.data
    counterparties.value = cpRes.data
  } finally {
    loading.value = false
  }
}

// Capital Accounts
function openAddAcct() {
  acctForm.value = { investor_id: null, committed_capital: 0, called_capital: 0, ownership_pct: 0 }
  isEditAcct.value = false
  editAcctId.value = null
  showAcctDialog.value = true
}
function openEditAcct(row: any) {
  acctForm.value = { ...row }
  isEditAcct.value = true
  editAcctId.value = row.id
  showAcctDialog.value = true
}
async function saveAcct() {
  if (!acctForm.value.investor_id) return
  if (isEditAcct.value && editAcctId.value) {
    await updateCapitalAccount(fundId.value, editAcctId.value, acctForm.value)
  } else {
    await createCapitalAccount(fundId.value, companyId.value, acctForm.value)
  }
  showAcctDialog.value = false
  await loadAll()
}
async function removeAcct(id: number) {
  if (!confirm('确定删除？')) return
  await deleteCapitalAccount(fundId.value, id)
  await loadAll()
}

// Capital Calls
function openAddCall() {
  callForm.value = { call_date: '', call_amount: 0, due_date: '', notes: '' }
  showCallDialog.value = true
}
async function saveCall() {
  if (!callForm.value.call_date || !callForm.value.call_amount) return
  await createCapitalCall(fundId.value, companyId.value, callForm.value)
  showCallDialog.value = false
  await loadAll()
}
async function removeCall(id: number) {
  if (!confirm('确定删除？关联凭证将一并删除。')) return
  await deleteCapitalCall(fundId.value, id)
  await loadAll()
}

// Distributions
function openAddDist() {
  distForm.value = { distribution_date: '', amount: 0, distribution_type: 'income', notes: '' }
  showDistDialog.value = true
}
async function saveDist() {
  if (!distForm.value.distribution_date || !distForm.value.amount) return
  await createFundDistribution(fundId.value, companyId.value, distForm.value)
  showDistDialog.value = false
  await loadAll()
}
async function removeDist(id: number) {
  if (!confirm('确定删除？关联凭证将一并删除。')) return
  await deleteFundDistribution(fundId.value, id)
  await loadAll()
}

const totalCalled = computed(() => accounts.value.reduce((s, a) => s + (a.called_capital || 0), 0))
const totalCommitted = computed(() => accounts.value.reduce((s, a) => s + (a.committed_capital || 0), 0))
const totalDistributed = computed(() => distributions.value.reduce((s, d) => s + (d.amount || 0), 0))
const pendingCalls = computed(() =>
  calls.value.filter(c => c.status === 'pending').reduce((s, c) => s + (c.call_amount || 0), 0),
)

onMounted(loadAll)
</script>

<template>
  <div class="p-4 space-y-6">
    <div class="flex items-center gap-4">
      <Button icon="pi pi-arrow-left" severity="secondary" text rounded @click="router.push('/investments/funds')" />
      <h2 class="text-lg font-semibold text-zinc-700">{{ fund?.fund_name || '基金详情' }}</h2>
      <Tag v-if="fund" :value="fund.fund_type" severity="info" class="text-xs" />
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-4 gap-4">
      <Card class="shadow-sm"
        ><template #content
          ><div class="text-sm text-stone-500">LP数</div>
          <div class="text-xl font-bold text-stone-800">{{ accounts.length }}</div></template
        ></Card
      >
      <Card class="shadow-sm"
        ><template #content
          ><div class="text-sm text-stone-500">承诺出资</div>
          <div class="text-xl font-bold text-stone-800">¥{{ totalCommitted.toLocaleString() }}</div></template
        ></Card
      >
      <Card class="shadow-sm"
        ><template #content
          ><div class="text-sm text-stone-500">已实缴</div>
          <div class="text-xl font-bold text-indigo-600">¥{{ totalCalled.toLocaleString() }}</div></template
        ></Card
      >
      <Card class="shadow-sm"
        ><template #content
          ><div class="text-sm text-stone-500">待缴付/已分配</div>
          <div class="text-xl font-bold">
            <span class="text-amber-600">¥{{ pendingCalls.toLocaleString() }}</span
            ><span class="text-stone-300 mx-1">/</span
            ><span class="text-emerald-600">¥{{ totalDistributed.toLocaleString() }}</span>
          </div></template
        ></Card
      >
    </div>

    <!-- LP Capital Accounts -->
    <div class="bg-white rounded-lg border border-stone-200 p-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-semibold text-zinc-700">LP 资本账户</h3>
        <Button label="添加 LP" icon="pi pi-plus" size="small" @click="openAddAcct" />
      </div>
      <DataTable :value="accounts" :loading="loading" stripedRows size="small">
        <Column header="投资人"
          ><template #body="{ data }">{{ getInvestorName(data.investor_id) }}</template></Column
        >
        <Column header="承诺出资"
          ><template #body="{ data }">¥{{ data.committed_capital?.toLocaleString() }}</template></Column
        >
        <Column header="已实缴"
          ><template #body="{ data }">¥{{ data.called_capital?.toLocaleString() }}</template></Column
        >
        <Column header="占比"
          ><template #body="{ data }">{{ data.ownership_pct?.toFixed(1) }}%</template></Column
        >
        <Column header="操作" style="width: 100px">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button icon="pi pi-pencil" size="small" severity="secondary" text rounded @click="openEditAcct(data)" />
              <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="removeAcct(data.id)" />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Capital Calls -->
    <div class="bg-white rounded-lg border border-stone-200 p-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-semibold text-zinc-700">资本召唤</h3>
        <Button label="发起召唤" icon="pi pi-plus" size="small" @click="openAddCall" />
      </div>
      <DataTable :value="calls" :loading="loading" stripedRows size="small">
        <Column field="call_date" header="日期" sortable />
        <Column header="金额"
          ><template #body="{ data }">¥{{ data.call_amount?.toLocaleString() }}</template></Column
        >
        <Column field="due_date" header="截止日" />
        <Column header="状态"
          ><template #body="{ data }"
            ><Tag
              :value="data.status === 'pending' ? '待缴' : data.status === 'paid' ? '已缴' : '逾期'"
              :severity="
                data.status === 'paid' ? 'success' : data.status === 'pending' ? 'warn' : 'danger'
              " /></template
        ></Column>
        <Column header="凭证"
          ><template #body="{ data }"
            ><span v-if="data.voucher_id" class="text-blue-600">#{{ data.voucher_id }}</span
            ><span v-else class="text-stone-300">-</span></template
          ></Column
        >
        <Column field="notes" header="备注" />
        <Column header="操作" style="width: 60px">
          <template #body="{ data }"
            ><Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="removeCall(data.id)"
          /></template>
        </Column>
      </DataTable>
    </div>

    <!-- Distributions -->
    <div class="bg-white rounded-lg border border-stone-200 p-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-semibold text-zinc-700">基金分配</h3>
        <Button label="记录分配" icon="pi pi-plus" size="small" @click="openAddDist" />
      </div>
      <DataTable :value="distributions" :loading="loading" stripedRows size="small">
        <Column field="distribution_date" header="日期" sortable />
        <Column field="distribution_type" header="类型"
          ><template #body="{ data }"
            ><Tag
              :value="
                data.distribution_type === 'income'
                  ? '收益'
                  : data.distribution_type === 'return_of_capital'
                    ? '返还本金'
                    : 'Carry'
              "
              :severity="data.distribution_type === 'income' ? 'success' : 'info'" /></template
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
        <Column field="notes" header="备注" />
        <Column header="操作" style="width: 60px">
          <template #body="{ data }"
            ><Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="removeDist(data.id)"
          /></template>
        </Column>
      </DataTable>
    </div>

    <!-- Dialogs: Capital Account -->
    <Dialog
      v-model:visible="showAcctDialog"
      :header="isEditAcct ? '编辑LP' : '添加LP'"
      :style="{ width: '420px' }"
      modal
    >
      <div class="flex flex-col gap-3 pt-2">
        <div>
          <label class="text-sm text-stone-600">投资人 *</label
          ><Dropdown
            v-model="acctForm.investor_id"
            :options="counterparties"
            optionLabel="name"
            optionValue="id"
            class="w-full"
            filter
            :disabled="isEditAcct"
          />
        </div>
        <div>
          <label class="text-sm text-stone-600">承诺出资</label
          ><InputNumber v-model="acctForm.committed_capital" mode="currency" currency="CNY" class="w-full" />
        </div>
        <div>
          <label class="text-sm text-stone-600">已实缴</label
          ><InputNumber v-model="acctForm.called_capital" mode="currency" currency="CNY" class="w-full" />
        </div>
        <div>
          <label class="text-sm text-stone-600">占比 (%)</label
          ><InputNumber v-model="acctForm.ownership_pct" suffix="%" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showAcctDialog = false" /><Button
          label="保存"
          @click="saveAcct"
          :disabled="!acctForm.investor_id"
      /></template>
    </Dialog>

    <!-- Dialog: Capital Call -->
    <Dialog v-model:visible="showCallDialog" header="发起资本召唤" :style="{ width: '420px' }" modal>
      <div class="flex flex-col gap-3 pt-2">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">日期 *</label
            ><InputText v-model="callForm.call_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
          <div>
            <label class="text-sm text-stone-600">截止日</label
            ><InputText v-model="callForm.due_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
        </div>
        <div>
          <label class="text-sm text-stone-600">金额 *</label
          ><InputNumber v-model="callForm.call_amount" mode="currency" currency="CNY" class="w-full" />
        </div>
        <div>
          <label class="text-sm text-stone-600">备注</label
          ><Textarea v-model="callForm.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showCallDialog = false" /><Button
          label="保存并生成凭证"
          @click="saveCall"
          :disabled="!callForm.call_date || !callForm.call_amount"
      /></template>
    </Dialog>

    <!-- Dialog: Distribution -->
    <Dialog v-model:visible="showDistDialog" header="记录分配" :style="{ width: '420px' }" modal>
      <div class="flex flex-col gap-3 pt-2">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-sm text-stone-600">日期 *</label
            ><InputText v-model="distForm.distribution_date" class="w-full" placeholder="YYYY-MM-DD" />
          </div>
          <div>
            <label class="text-sm text-stone-600">类型</label
            ><Dropdown
              v-model="distForm.distribution_type"
              :options="DIST_TYPES"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
        </div>
        <div>
          <label class="text-sm text-stone-600">金额 *</label
          ><InputNumber v-model="distForm.amount" mode="currency" currency="CNY" class="w-full" />
        </div>
        <div>
          <label class="text-sm text-stone-600">备注</label
          ><Textarea v-model="distForm.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showDistDialog = false" /><Button
          label="保存并生成凭证"
          @click="saveDist"
          :disabled="!distForm.distribution_date || !distForm.amount"
      /></template>
    </Dialog>
  </div>
</template>
