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
import {
  listPortfolios,
  listPositions,
  listAccounts,
  listCounterparties,
  createPosition,
  updatePosition,
  deletePosition,
} from '@/api'

const portfolios = ref<any[]>([])
const accounts = ref<any[]>([])
const counterparties = ref<any[]>([])
const positions = ref<any[]>([])
const filterPortfolio = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const ACCOUNT_OPTIONS = computed(() =>
  accounts.value
    .filter((a: any) => ['1101', '1501', '1503', '1511'].some(c => a.code.startsWith(c)))
    .map((a: any) => ({ label: `${a.code} ${a.name}`, value: a.code })),
)

const STATUS_LABELS: Record<string, string> = { active: '活跃', exited: '已退出', impaired: '已减值' }
const emptyForm = () => ({
  portfolio_id: filterPortfolio.value || null,
  account_code: '',
  security_name: '',
  security_code: '',
  quantity: 0,
  unit_cost: 0,
  cost_amount: 0,
  fair_value: 0,
  fair_value_date: '',
  valuation_method: 'cost',
  counterparty_id: null,
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [pRes, aRes, cRes, posRes] = await Promise.all([
      listPortfolios(companyId.value),
      listAccounts(companyId.value),
      listCounterparties(companyId.value),
      listPositions(companyId.value, filterPortfolio.value || undefined),
    ])
    portfolios.value = pRes.data
    accounts.value = aRes.data
    counterparties.value = cRes.data
    positions.value = posRes.data
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    portfolio_id: row.portfolio_id,
    account_code: row.account_code,
    security_name: row.security_name,
    security_code: row.security_code || '',
    quantity: row.quantity,
    unit_cost: row.unit_cost,
    cost_amount: row.cost_amount,
    fair_value: row.fair_value,
    fair_value_date: row.fair_value_date || '',
    valuation_method: row.valuation_method,
    counterparty_id: row.counterparty_id,
  }
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.security_name || !form.value.account_code) return
  saving.value = true
  try {
    if (editingId.value) {
      await updatePosition(editingId.value, form.value)
    } else {
      await createPosition(companyId.value, form.value)
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
  if (!confirm('确认删除该持仓？')) return
  try {
    await deletePosition(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
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
        <h2 class="text-lg font-semibold text-zinc-700">投资持仓</h2>
        <Dropdown
          v-model="filterPortfolio"
          :options="portfolios"
          optionLabel="name"
          optionValue="id"
          placeholder="全部组合"
          class="w-48"
          @change="onFilterChange"
          showClear
        />
      </div>
      <Button label="新增持仓" icon="pi pi-plus" @click="openAdd" />
    </div>

    <DataTable :value="positions" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="security_name" header="标的名称" sortable />
      <Column field="security_code" header="代码" sortable style="width: 100px" />
      <Column field="account_code" header="科目" sortable style="width: 100px" />
      <Column field="quantity" header="数量" sortable style="width: 100px">
        <template #body="{ data }">{{ data.quantity.toLocaleString() }}</template>
      </Column>
      <Column field="cost_amount" header="成本" sortable style="width: 120px">
        <template #body="{ data }">{{ data.cost_amount.toLocaleString() }}</template>
      </Column>
      <Column field="fair_value" header="公允价值" sortable style="width: 120px">
        <template #body="{ data }">{{ data.fair_value.toLocaleString() }}</template>
      </Column>
      <Column header="未实现损益" style="width: 120px">
        <template #body="{ data }">
          <span :class="data.fair_value - data.cost_amount >= 0 ? 'text-green-600' : 'text-red-600'">
            {{ (data.fair_value - data.cost_amount).toLocaleString() }}
          </span>
        </template>
      </Column>
      <Column field="status" header="状态" sortable style="width: 80px">
        <template #body="{ data }">
          <Tag
            :value="STATUS_LABELS[data.status] || data.status"
            :severity="data.status === 'active' ? 'success' : data.status === 'exited' ? 'warn' : 'danger'"
          />
        </template>
      </Column>
      <Column header="操作" style="width: 140px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" text size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑持仓' : '新增持仓'" :modal="true" class="w-[500px]">
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">所属组合</label
            ><Dropdown
              v-model="form.portfolio_id"
              :options="portfolios"
              optionLabel="name"
              optionValue="id"
              class="w-full"
            />
          </div>
          <div>
            <label class="block text-sm mb-1">会计科目 *</label
            ><Dropdown
              v-model="form.account_code"
              :options="ACCOUNT_OPTIONS"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              filter
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">标的名称 *</label
            ><InputText v-model="form.security_name" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">代码</label><InputText v-model="form.security_code" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="block text-sm mb-1">数量</label><InputNumber v-model="form.quantity" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">单位成本</label><InputNumber v-model="form.unit_cost" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">成本总额</label><InputNumber v-model="form.cost_amount" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="block text-sm mb-1">公允价值</label><InputNumber v-model="form.fair_value" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">估值日期</label
            ><InputText v-model="form.fair_value_date" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">估值方法</label>
            <Dropdown
              v-model="form.valuation_method"
              :options="[
                { label: '市价', value: 'market_price' },
                { label: '成本', value: 'cost' },
                { label: 'DCF', value: 'dcf' },
                { label: '可比', value: 'comparables' },
              ]"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
        </div>
        <div>
          <label class="block text-sm mb-1">被投资方</label
          ><Dropdown
            v-model="form.counterparty_id"
            :options="counterparties"
            optionLabel="name"
            optionValue="id"
            class="w-full"
            showClear
          />
        </div>
      </div>
      <template #footer>
        <Button label="取消" text @click="showDialog = false" />
        <Button label="保存" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
