<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from '@/i18n'
import { useRoute } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Calendar from 'primevue/calendar'
import { listDeclarations, createDeclaration, updateDeclaration, deleteDeclaration } from '@/api/taxes'

const route = useRoute()
const { t } = useI18n()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const taxTypeMap: Record<string, string> = {
  vat: '增值税',
  urban: '城市维护建设税',
  education: '教育费附加',
  local_edu: '地方教育附加',
  corporate_income: '企业所得税',
  iit: '个人所得税代扣代缴',
  stamp_duty: '印花税',
  property_tax: '房产税',
  land_use_tax: '土地使用税',
  vehicle_tax: '车船税',
  land_vat: '土地增值税',
  penalty: '罚款与滞纳金',
}

const taxType = computed(() => {
  const p = route.path
  if (p.includes('/surcharge/urban')) return 'urban'
  if (p.includes('/surcharge/education')) return 'education'
  if (p.includes('/surcharge/local-edu')) return 'local_edu'
  if (p.includes('/corporate-income')) return 'corporate_income'
  if (p.includes('/iit')) return 'iit'
  if (p.includes('/stamp-duty')) return 'stamp_duty'
  if (p.includes('/property-tax')) return 'property_tax'
  if (p.includes('/land-use-tax')) return 'land_use_tax'
  if (p.includes('/vehicle-tax')) return 'vehicle_tax'
  if (p.includes('/land-vat')) return 'land_vat'
  if (p.includes('/penalty')) return 'penalty'
  if (p.includes('/vat')) return 'vat'
  return 'vat'
})

const pageTitle = computed(() => taxTypeMap[taxType.value] || taxType.value)
const isPenalty = computed(() => taxType.value === 'penalty')

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const search = ref('')

const statusOptions = [
  { label: '待申报', value: 'pending' },
  { label: '已申报', value: 'filed' },
  { label: '已缴纳', value: 'paid' },
]

const emptyForm = () => ({
  company_id: companyId.value,
  tax_type: taxType.value,
  period_start: new Date() as Date | null,
  period_end: new Date() as Date | null,
  tax_base: null as number | null,
  tax_rate: null as number | null,
  tax_amount: 0,
  paid_amount: 0,
  status: 'pending',
  declaration_date: null as Date | null,
  payment_deadline: null as Date | null,
  payment_date: null as Date | null,
  notes: '',
})
const form = ref(emptyForm())

function fmtDate(d: Date | null): string | undefined {
  if (!d) return undefined
  return d.toISOString().slice(0, 10)
}

async function load() {
  loading.value = true
  try {
    const res = await listDeclarations({
      company_id: companyId.value,
      tax_type: taxType.value,
    })
    items.value = res.data
  } finally {
    loading.value = false
  }
}

const filteredItems = computed(() => {
  if (!search.value) return items.value
  const q = search.value.toLowerCase()
  return items.value.filter((i: any) => (i.notes || '').toLowerCase().includes(q))
})

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    company_id: row.company_id,
    tax_type: row.tax_type,
    period_start: row.period_start ? new Date(row.period_start) : null,
    period_end: row.period_end ? new Date(row.period_end) : null,
    tax_base: row.tax_base,
    tax_rate: row.tax_rate,
    tax_amount: row.tax_amount || 0,
    paid_amount: row.paid_amount || 0,
    status: row.status,
    declaration_date: row.declaration_date ? new Date(row.declaration_date) : null,
    payment_deadline: row.payment_deadline ? new Date(row.payment_deadline) : null,
    payment_date: row.payment_date ? new Date(row.payment_date) : null,
    notes: row.notes || '',
  }
  showDialog.value = true
}

function buildPayload() {
  return {
    ...form.value,
    period_start: fmtDate(form.value.period_start),
    period_end: fmtDate(form.value.period_end),
    declaration_date: fmtDate(form.value.declaration_date),
    payment_deadline: fmtDate(form.value.payment_deadline),
    payment_date: fmtDate(form.value.payment_date),
  }
}

async function handleSave() {
  if (!form.value.tax_type) return
  try {
    const payload = buildPayload()
    if (editingId.value) {
      await updateDeclaration(editingId.value, payload)
    } else {
      await createDeclaration(payload)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.saveFailed'))
  }
}

async function handleDelete(id: number) {
  if (!confirm(t('common.deleteConfirm'))) return
  try {
    await deleteDeclaration(id)
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
      <h2 class="text-lg font-bold text-zinc-700">{{ pageTitle }}</h2>
      <div class="flex gap-2">
        <InputText v-model="search" placeholder="搜索备注..." class="w-48" />
        <Button :label="t('common.search')" icon="pi pi-search" severity="secondary" @click="load" />
        <Button :label="t('common.add')" icon="pi pi-plus" @click="openAdd" />
      </div>
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="filteredItems" :loading="loading" stripedRows paginator :rows="15" class="shadow-sm">
        <Column header="序号" style="width: 60px">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column header="计税期间" style="width: 200px">
          <template #body="{ data }">
            {{ data.period_start?.slice(0, 10) || '-' }} ~ {{ data.period_end?.slice(0, 10) || '-' }}
          </template>
        </Column>
        <Column v-if="!isPenalty" field="tax_base" header="税基" style="width: 120px">
          <template #body="{ data }">
            {{ data.tax_base != null ? `¥${Number(data.tax_base).toLocaleString()}` : '-' }}
          </template>
        </Column>
        <Column v-if="!isPenalty" field="tax_rate" :header="t('accounting.taxes_page.taxRate')" style="width: 70px">
          <template #body="{ data }">
            {{ data.tax_rate != null ? `${data.tax_rate}%` : '-' }}
          </template>
        </Column>
        <Column field="tax_amount" :header="t('accounting.taxes_page.taxAmount')" style="width: 120px">
          <template #body="{ data }">¥{{ Number(data.tax_amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="paid_amount" header="已缴金额" style="width: 120px">
          <template #body="{ data }">¥{{ Number(data.paid_amount || 0).toLocaleString() }}</template>
        </Column>
        <Column header="未缴金额" style="width: 120px">
          <template #body="{ data }">
            ¥{{ (Number(data.tax_amount || 0) - Number(data.paid_amount || 0)).toLocaleString() }}
          </template>
        </Column>
        <Column field="status" :header="t('common.status')" style="width: 80px">
          <template #body="{ data }">
            <span
              :class="{
                'text-amber-600': data.status === 'pending',
                'text-blue-600': data.status === 'filed',
                'text-green-600': data.status === 'paid',
              }"
            >
              {{ data.status === 'pending' ? '待申报' : data.status === 'filed' ? '已申报' : '已缴纳' }}
            </span>
          </template>
        </Column>
        <Column header="申报日期" style="width: 110px">
          <template #body="{ data }">{{ data.declaration_date?.slice(0, 10) || '-' }}</template>
        </Column>
        <Column header="缴纳日期" style="width: 110px">
          <template #body="{ data }">{{ data.payment_date?.slice(0, 10) || '-' }}</template>
        </Column>
        <Column :header="t('common.actions')" style="width: 130px">
          <template #body="{ data }">
            <Button :label="t('common.edit')" text severity="info" size="small" @click="openEdit(data)" />
            <Button :label="t('common.delete')" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog
      v-model:visible="showDialog"
      :header="editingId ? '编辑申报记录' : '新增申报记录'"
      :style="{ width: '780px' }"
    >
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">计税期间 *</label>
            <div class="flex gap-2 items-center">
              <Calendar v-model="form.period_start" class="flex-1" placeholder="起" />
              <span class="text-zinc-400">~</span>
              <Calendar v-model="form.period_end" class="flex-1" placeholder="止" />
            </div>
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">{{ t('common.status') }}</label>
            <Select
              v-model="form.status"
              :options="statusOptions"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
        </div>
        <div v-if="!isPenalty" class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税基（计税依据）</label>
            <input
              type="number"
              v-model.number="form.tax_base"
              class="w-full border border-stone-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税率（%）</label>
            <input
              type="number"
              v-model.number="form.tax_rate"
              class="w-full border border-stone-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">{{ t('accounting.taxes_page.taxAmount') }} *</label>
            <input
              type="number"
              v-model.number="form.tax_amount"
              class="w-full border border-stone-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">已缴金额</label>
            <input
              type="number"
              v-model.number="form.paid_amount"
              class="w-full border border-stone-300 rounded px-3 py-2 text-sm"
            />
          </div>
        </div>
        <div v-else class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">罚款金额 *</label>
            <input
              type="number"
              v-model.number="form.tax_amount"
              class="w-full border border-stone-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">已缴金额</label>
            <input
              type="number"
              v-model.number="form.paid_amount"
              class="w-full border border-stone-300 rounded px-3 py-2 text-sm"
            />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">申报日期</label>
            <Calendar v-model="form.declaration_date" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">缴纳截止日</label>
            <Calendar v-model="form.payment_deadline" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">实际缴纳日</label>
            <Calendar v-model="form.payment_date" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">{{ t('common.remark') }}</label>
          <InputText v-model="form.notes" class="w-full" />
        </div>
        <div>
          <Button :label="t('common.save')" icon="pi pi-check" @click="handleSave" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
