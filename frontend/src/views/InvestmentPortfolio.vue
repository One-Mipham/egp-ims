<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import { listPortfolios, createPortfolio, updatePortfolio, deletePortfolio } from '@/api'
import { useI18n } from '@/i18n'

const portfolios = ref<any[]>([])
const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const INVEST_TYPES = [
  { label: '风险投资 VC', value: 'vc' },
  { label: '私募股权 PE', value: 'pe' },
  { label: '天使投资', value: 'angel' },
  { label: '一般股权投资', value: 'general_equity' },
  { label: '二级市场投资', value: 'secondary_market' },
  { label: '固定收益（债券）', value: 'fixed_income' },
  { label: '公募基金', value: 'mutual_fund' },
  { label: '私募基金', value: 'private_fund' },
  { label: 'ETF', value: 'etf' },
  { label: '另类资产', value: 'alternative' },
  { label: '房地产', value: 'real_estate' },
  { label: '基础设施', value: 'infrastructure' },
  { label: '私募信贷', value: 'private_credit' },
  { label: '大宗商品', value: 'commodity' },
  { label: '数字资产', value: 'digital_asset' },
  { label: '信托', value: 'trust' },
  { label: '衍生品', value: 'derivatives' },
]

const TYPE_LABELS: Record<string, string> = {
  vc: 'VC',
  pe: 'PE',
  angel: '天使',
  general_equity: '一般股权',
  secondary_market: '二级市场',
  fixed_income: '固定收益',
  mutual_fund: '公募基金',
  private_fund: '私募基金',
  etf: 'ETF',
  alternative: '另类',
  real_estate: '房地产',
  infrastructure: '基础设施',
  private_credit: '私募信贷',
  commodity: '大宗商品',
  digital_asset: '数字资产',
  trust: '信托',
  derivatives: '衍生品',
}

const STATUS_LABELS: Record<string, string> = {
  active: '活跃',
  closed: '已关闭',
  liquidated: '已清算',
}

const emptyForm = () => ({ name: '', investment_type: 'general_equity', currency: 'CNY', description: '' })
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const res = await listPortfolios(companyId.value)
    portfolios.value = res.data
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
    name: row.name,
    investment_type: row.investment_type,
    currency: row.currency,
    description: row.description || '',
  }
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.name) return
  saving.value = true
  try {
    if (editingId.value) {
      await updatePortfolio(editingId.value, form.value)
    } else {
      await createPortfolio(companyId.value, form.value)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除该投资组合？组合下的持仓也会被删除。')) return
  try {
    await deletePortfolio(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.deleteFailed'))
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">{{ t('investments.portfolios') }}</h2>
      <Button label="新增组合" icon="pi pi-plus" @click="openAdd" />
    </div>

    <DataTable :value="portfolios" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="name" :header="t('investments.portfolioName')" sortable />
      <Column field="investment_type" header="投资类型" sortable>
        <template #body="{ data }">
          <Tag :value="TYPE_LABELS[data.investment_type] || data.investment_type" />
        </template>
      </Column>
      <Column field="currency" header="币种" sortable style="width: 80px" />
      <Column field="status" :header="t('common.status')" sortable style="width: 100px">
        <template #body="{ data }">
          <Tag
            :value="STATUS_LABELS[data.status] || data.status"
            :severity="data.status === 'active' ? 'success' : data.status === 'closed' ? 'warn' : 'danger'"
          />
        </template>
      </Column>
      <Column field="description" :header="t('common.remark')" />
      <Column :header="t('common.actions')" style="width: 140px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" text size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑组合' : '新增组合'" :modal="true" class="w-[450px]">
      <div class="flex flex-col gap-3">
        <div><label class="block text-sm mb-1">组合名称 *</label><InputText v-model="form.name" class="w-full" /></div>
        <div>
          <label class="block text-sm mb-1">投资类型</label
          ><Dropdown
            v-model="form.investment_type"
            :options="INVEST_TYPES"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-sm mb-1">币种</label
          ><Dropdown
            v-model="form.currency"
            :options="[
              { label: 'CNY', value: 'CNY' },
              { label: 'USD', value: 'USD' },
              { label: 'HKD', value: 'HKD' },
            ]"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>
        <div><label class="block text-sm mb-1">{{ t('common.remark') }}</label><Textarea v-model="form.description" rows="2" class="w-full" /></div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="showDialog = false" />
        <Button :label="t('common.save')" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
