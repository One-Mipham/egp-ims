<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import {
  listVouchers,
  createVoucher,
  updateVoucher,
  approveVoucher,
  postVoucher,
  reverseVoucher,
  unapproveVoucher,
  unpostVoucher,
  unreverseVoucher,
  listAccounts,
  listDepartments,
  listCounterparties,
  listPersons,
  listProjects,
} from '@/api'
import { useI18n } from '@/i18n'

const vouchers = ref<any[]>([])
const accounts = ref<any[]>([])
const departments = ref<any[]>([])
const counterparties = ref<any[]>([])
const persons = ref<any[]>([])
const projects = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showReverseDialog = ref(false)
const showQueryDialog = ref(false)
const showBatchApproveDialog = ref(false)
const showDetailDialog = ref(false)
const detailVoucher = ref<any>(null)
const reverseReason = ref('')
const reverseTarget = ref<number | null>(null)
const editTarget = ref<any>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const companyName = computed(() => localStorage.getItem('companyName') || '')
const { t } = useI18n()

const selectedEntryIdx = ref(0)

const accountMap = computed(() => {
  const m: Record<string, { name: string; level: number }> = {}
  for (const a of accounts.value) m[a.code] = { name: a.name, level: a.level }
  return m
})

function getLevel1Name(code: string): string {
  if (!code || code.length < 4) return ''
  return accountMap.value[code.substring(0, 4)]?.name || ''
}

function getDetailName(code: string): string {
  if (!code) return ''
  const acct = accountMap.value[code]
  return acct && acct.level > 1 ? acct.name : ''
}

const selectedEntryAux = computed(() => {
  const entry = voucherForm.value.entries[selectedEntryIdx.value]
  if (!entry || !entry.account_code) return null
  return accountAuxConfig.value[entry.account_code] || null
})

function blankEntry() {
  return {
    account_code: '',
    debit: 0,
    credit: 0,
    department_id: null,
    counterparty_id: null,
    person_id: null,
    project_id: null,
    description: '',
  }
}
const defaultForm = () => ({
  date: localStorage.getItem('accountingDate') || '',
  voucher_type: 'transfer',
  summary: '',
  entries: Array.from({ length: 4 }, () => blankEntry()),
})
const voucherForm = ref(defaultForm())
const editForm = ref(defaultForm())

const voucherNoPreview = computed(() => {
  const d = voucherForm.value.date
  const ym = d ? d.replace(/-/g, '').substring(0, 6) : '______'
  const label = TYPE_LABELS[voucherForm.value.voucher_type] || '转'
  return `${label}字第 ${ym}-____ 号`
})

watch(
  () => voucherForm.value.entries.length,
  () => {
    if (selectedEntryIdx.value >= voucherForm.value.entries.length)
      selectedEntryIdx.value = Math.max(0, voucherForm.value.entries.length - 1)
  },
)

const accountAuxConfig = computed(() => {
  const map: Record<string, any> = {}
  for (const a of accounts.value)
    map[a.code] = {
      dept: !!a.aux_dept,
      person: !!a.aux_person,
      counterparty: !!a.aux_counterparty,
      project: !!a.aux_project,
    }
  return map
})

function getPersonsForEntry(entry: any) {
  if (!entry.department_id) return persons.value
  const dept = departments.value.find((d: any) => d.id === entry.department_id)
  if (!dept) return persons.value
  return persons.value.filter((p: any) => p.department_code === dept.code)
}

// Query filters
const queryFilters = ref({ start_date: '', end_date: '', voucher_no: '', voucher_type: '', status: '' })

// Batch approve selection
const selectedForApprove = ref<any[]>([])

const STATUS_LABELS: Record<string, string> = {
  draft: t('accounting.vouchers_page.draft'),
  approved: t('accounting.vouchers_page.approved'),
  posted: t('accounting.vouchers_page.posted'),
  reversed: t('accounting.vouchers_page.reversed'),
}
const TYPE_LABELS: Record<string, string> = { receipt: t('accounting.vouchers_page.receipt'), payment: t('accounting.vouchers_page.payment'), transfer: t('accounting.vouchers_page.transfer') }
const STATUS_OPTIONS = [
  { label: t('common.all'), value: '' },
  { label: t('accounting.vouchers_page.draft'), value: 'draft' },
  { label: t('accounting.vouchers_page.approved'), value: 'approved' },
  { label: t('accounting.vouchers_page.posted'), value: 'posted' },
  { label: t('accounting.vouchers_page.reversed'), value: 'reversed' },
]
const TYPE_OPTIONS = [
  { label: t('common.all'), value: '' },
  { label: t('accounting.vouchers_page.receipt'), value: 'receipt' },
  { label: t('accounting.vouchers_page.payment'), value: 'payment' },
  { label: t('accounting.vouchers_page.transfer'), value: 'transfer' },
]

const CATEGORY_LABELS: Record<string, string> = {
  asset: '资产',
  liability: '负债',
  equity: '权益',
  cost: '成本',
  revenue: '收入',
  expense: '费用',
}

const LEVEL_INDENT = ['', '  ', '    ', '      ']

const groupedAccounts = computed(() => {
  const groups: Record<string, any[]> = { asset: [], liability: [], equity: [], revenue: [], expense: [] }
  for (const a of accounts.value) {
    if (a.category === 'profit_loss') {
      const name = a.name || ''
      const isRevenue = name.includes('收入') || name.includes('收益') || name.includes('利息')
      groups[isRevenue ? 'revenue' : 'expense'].push(a)
    } else {
      const cat = a.category || 'asset'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(a)
    }
  }
  return ['asset', 'liability', 'equity', 'revenue', 'cost', 'expense']
    .filter(cat => groups[cat].length > 0)
    .map(cat => ({
      label: CATEGORY_LABELS[cat],
      accounts: groups[cat].map(a => ({
        ...a,
        display: `${a.code} ${LEVEL_INDENT[(a.level || 1) - 1]}${a.name}`,
      })),
    }))
})

async function loadVouchers() {
  loading.value = true
  try {
    const params: any = {}
    if (queryFilters.value.start_date) params.start_date = queryFilters.value.start_date
    if (queryFilters.value.end_date) params.end_date = queryFilters.value.end_date
    if (queryFilters.value.voucher_no) params.voucher_no = queryFilters.value.voucher_no
    if (queryFilters.value.voucher_type) params.voucher_type = queryFilters.value.voucher_type
    if (queryFilters.value.status) params.status = queryFilters.value.status
    const res = await listVouchers(companyId.value, Object.keys(params).length ? params : undefined)
    vouchers.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadMeta() {
  try {
    const [a, d, c, p, pr] = await Promise.all([
      listAccounts(companyId.value),
      listDepartments(companyId.value),
      listCounterparties(companyId.value),
      listPersons(companyId.value),
      listProjects(companyId.value),
    ])
    accounts.value = a.data
    departments.value = d.data
    counterparties.value = c.data
    persons.value = p.data
    projects.value = pr.data
  } catch {}
}

function addEntry(form: any) {
  form.entries.push({
    account_code: '',
    debit: 0,
    credit: 0,
    department_id: null,
    counterparty_id: null,
    person_id: null,
    project_id: null,
    description: '',
  })
}

function removeEntry(form: any, idx: number) {
  if (form.entries.length > 1) form.entries.splice(idx, 1)
}

function _calcTotals(entries: any[]) {
  const debit = entries.reduce((s, e) => s + (Number(e.debit) || 0), 0)
  const credit = entries.reduce((s, e) => s + (Number(e.credit) || 0), 0)
  return { debit, credit, balanced: Math.abs(debit - credit) < 0.005 && debit > 0 }
}

const totalDebit = computed(() => voucherForm.value.entries.reduce((s, e) => s + (Number(e.debit) || 0), 0))
const totalCredit = computed(() => voucherForm.value.entries.reduce((s, e) => s + (Number(e.credit) || 0), 0))
const balanced = computed(() => Math.abs(totalDebit.value - totalCredit.value) < 0.005 && totalDebit.value > 0)

const editDebit = computed(() => editForm.value.entries.reduce((s, e) => s + (Number(e.debit) || 0), 0))
const editCredit = computed(() => editForm.value.entries.reduce((s, e) => s + (Number(e.credit) || 0), 0))
const editBalanced = computed(() => Math.abs(editDebit.value - editCredit.value) < 0.005 && editDebit.value > 0)
const selectedEditEntryIdx = ref(0)
const editSelectedAux = computed(() => {
  const entry = editForm.value.entries[selectedEditEntryIdx.value]
  if (!entry || !entry.account_code) return null
  return accountAuxConfig.value[entry.account_code] || null
})

function resetForm() {
  voucherForm.value = defaultForm()
  errorMsg.value = ''
  saving.value = false
}

async function handleCreate() {
  if (!balanced.value) return
  saving.value = true
  errorMsg.value = ''
  try {
    await createVoucher({
      company_id: companyId.value,
      date: voucherForm.value.date,
      voucher_type: voucherForm.value.voucher_type,
      summary: voucherForm.value.summary,
      entries: voucherForm.value.entries.map(e => ({
        account_code: e.account_code,
        department_id: e.department_id || undefined,
        counterparty_id: e.counterparty_id || undefined,
        person_id: e.person_id || undefined,
        project_id: e.project_id || undefined,
        debit: Number(e.debit) || 0,
        credit: Number(e.credit) || 0,
        description: e.description || undefined,
      })),
    })
    showAddDialog.value = false
    resetForm()
    await loadVouchers()
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || '创建失败'
    saving.value = false
  }
}

function openEdit(v: any) {
  editTarget.value = v
  editForm.value = {
    date: v.date,
    voucher_type: v.voucher_type,
    summary: v.summary,
    entries: v.entries.map((e: any) => ({
      account_code: e.account_code,
      debit: e.debit,
      credit: e.credit,
      department_id: e.department_id,
      counterparty_id: e.counterparty_id,
      person_id: e.person_id,
      project_id: e.project_id,
      description: e.description || '',
    })),
  }
  showEditDialog.value = true
}

async function handleEdit() {
  if (!editBalanced.value || !editTarget.value) return
  saving.value = true
  try {
    await updateVoucher(editTarget.value.id, {
      date: editForm.value.date,
      voucher_type: editForm.value.voucher_type,
      summary: editForm.value.summary,
      entries: editForm.value.entries.map((e: any) => ({
        account_code: e.account_code,
        department_id: e.department_id || undefined,
        counterparty_id: e.counterparty_id || undefined,
        person_id: e.person_id || undefined,
        project_id: e.project_id || undefined,
        debit: Number(e.debit) || 0,
        credit: Number(e.credit) || 0,
        description: e.description || undefined,
      })),
    })
    showEditDialog.value = false
    await loadVouchers()
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || '修改失败'
    saving.value = false
  }
}

async function handleApprove(id: number) {
  try {
    await approveVoucher(id)
    await loadVouchers()
  } catch (e: any) {
    alert(e.response?.data?.detail)
  }
}

async function handleBatchApprove() {
  if (!selectedForApprove.value.length) return
  for (const v of selectedForApprove.value) {
    try {
      await approveVoucher(v.id)
    } catch {}
  }
  selectedForApprove.value = []
  showBatchApproveDialog.value = false
  await loadVouchers()
}

async function handlePost(id: number) {
  try {
    await postVoucher(id)
    await loadVouchers()
  } catch (e: any) {
    alert(e.response?.data?.detail)
  }
}

async function handleReverse() {
  if (!reverseTarget.value || !reverseReason.value) return
  try {
    await reverseVoucher(reverseTarget.value, reverseReason.value)
    showReverseDialog.value = false
    reverseReason.value = ''
    await loadVouchers()
  } catch (e: any) {
    alert(e.response?.data?.detail)
  }
}

async function handleUnapprove(id: number) {
  if (!confirm('确认取消审核？凭证将恢复为草稿状态，可重新修改。')) return
  try {
    await unapproveVoucher(id)
    await loadVouchers()
    if (detailVoucher.value && detailVoucher.value.id === id) {
      const updated = vouchers.value.find(v => v.id === id)
      if (updated) detailVoucher.value = updated
    }
  } catch (e: any) {
    alert(e.response?.data?.detail)
  }
}

async function handleUnpost(id: number) {
  if (!confirm('确认取消记账？凭证将恢复为审核通过状态。')) return
  try {
    await unpostVoucher(id)
    await loadVouchers()
    if (detailVoucher.value && detailVoucher.value.id === id) {
      const updated = vouchers.value.find(v => v.id === id)
      if (updated) detailVoucher.value = updated
    }
  } catch (e: any) {
    alert(e.response?.data?.detail)
  }
}

async function handleUnreverse(id: number) {
  if (!confirm('确认取消冲销？凭证将恢复为已记账状态。')) return
  try {
    await unreverseVoucher(id)
    await loadVouchers()
    if (detailVoucher.value && detailVoucher.value.id === id) {
      const updated = vouchers.value.find(v => v.id === id)
      if (updated) detailVoucher.value = updated
    }
  } catch (e: any) {
    alert(e.response?.data?.detail)
  }
}

function handleQuery() {
  showQueryDialog.value = false
  loadVouchers()
}
function resetQuery() {
  queryFilters.value = { start_date: '', end_date: '', voucher_no: '', voucher_type: '', status: '' }
  loadVouchers()
}

function _formatNumber(val: number | null) {
  if (val === null || val === undefined) return ''
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function doPrintVoucher() {
  window.print()
}

function onRowClick(event: any) {
  detailVoucher.value = event.data
  showDetailDialog.value = true
}

const totalDetailDebit = computed(() =>
  (detailVoucher.value?.entries || []).reduce((s: number, e: any) => s + (Number(e.debit) || 0), 0)
)
const totalDetailCredit = computed(() =>
  (detailVoucher.value?.entries || []).reduce((s: number, e: any) => s + (Number(e.credit) || 0), 0)
)

function getAccountName(code: string): string {
  if (!code) return ''
  const a = accounts.value.find((ac: any) => ac.code === code)
  return a ? a.name : ''
}

const draftVouchers = computed(() => vouchers.value.filter(v => v.status === 'draft'))

onMounted(() => {
  loadVouchers()
  loadMeta()
})
</script>

<template>
  <div>
    <div class="flex flex-col gap-3 mb-4">
      <div class="flex justify-between items-center">
        <Button
          :label="t('accounting.vouchers_page.addVoucher')"
          icon="pi pi-plus"
          @click="showAddDialog = true; resetForm()"
        />
      </div>
      <div class="flex gap-2">
        <Button
          :label="t('accounting.vouchers_page.approveVoucher')"
          icon="pi pi-check"
          severity="info"
          text
          @click="showBatchApproveDialog = true"
          :disabled="!draftVouchers.length"
        />
        <Button :label="t('accounting.vouchers_page.searchVoucher')" icon="pi pi-search" severity="secondary" text @click="showQueryDialog = true" />
        <Button :label="t('accounting.vouchers_page.printVoucher')" icon="pi pi-print" severity="secondary" text @click="doPrintVoucher" />
      </div>
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto max-w-fit min-w-full">
      <DataTable
        :value="vouchers"
        :loading="loading"
        stripedRows
        paginator
        :rows="15"
        class="shadow-sm"
        tableStyle="min-width: auto"
        @row-click="onRowClick"
      >
        <Column field="voucher_no" :header="t('accounting.vouchers_page.voucherNo')" sortable style="width: 140px" />
        <Column field="date" :header="t('accounting.vouchers_page.voucherDate')" sortable style="width: 90px" />
        <Column :header="t('accounting.vouchers_page.voucherType')" style="width: 60px">
          <template #body="{ data }">{{ TYPE_LABELS[data.voucher_type] || data.voucher_type }}</template>
        </Column>
        <Column field="summary" :header="t('accounting.vouchers_page.summary')" style="width: 280px" />
        <Column :header="t('accounting.vouchers_page.status')" style="width: 70px">
          <template #body="{ data }">
            <Tag
              :value="STATUS_LABELS[data.status] || data.status"
              :severity="
                data.status === 'posted'
                  ? 'success'
                  : data.status === 'approved'
                    ? 'info'
                    : data.status === 'reversed'
                      ? 'danger'
                      : 'warning'
              "
            />
          </template>
        </Column>
        <Column :header="t('common.amount')" style="width: 120px">
          <template #body="{ data }">
            <span class="font-number">
              {{ (data.entries || []).reduce((s: number, e: any) => s + (Number(e.debit) || 0), 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}
            </span>
          </template>
        </Column>
        <Column :header="t('common.actions')" style="width: 260px">
          <template #body="{ data }">
            <Button
              v-if="data.status === 'draft'"
              :label="t('common.edit')"
              text
              severity="secondary"
              size="small"
              @click="openEdit(data)"
            />
            <Button
              v-if="data.status === 'draft'"
              :label="t('accounting.vouchers_page.approveVoucher')"
              text
              severity="info"
              size="small"
              @click="handleApprove(data.id)"
            />
            <Button
              v-if="data.status === 'approved'"
              :label="t('accounting.vouchers_page.unapproveVoucher')"
              text
              severity="warning"
              size="small"
              @click="handleUnapprove(data.id)"
            />
            <Button
              v-if="data.status === 'draft' || data.status === 'approved'"
              :label="t('accounting.vouchers_page.postVoucher')"
              text
              severity="success"
              size="small"
              @click="handlePost(data.id)"
            />
            <Button
              v-if="data.status === 'posted'"
              :label="t('accounting.vouchers_page.unpostVoucher')"
              text
              severity="warning"
              size="small"
              @click="handleUnpost(data.id)"
            />
            <Button
              v-if="data.status === 'posted'"
              :label="t('accounting.vouchers_page.reverseVoucher')"
              text
              severity="danger"
              size="small"
              @click="reverseTarget = data.id; reverseReason = ''; showReverseDialog = true"
            />
            <Button
              v-if="data.status === 'reversed'"
              :label="t('accounting.vouchers_page.unreverseVoucher')"
              text
              severity="warning"
              size="small"
              @click="handleUnreverse(data.id)"
            />
            <span
              v-if="data.status === 'closed'"
              class="text-xs text-zinc-400 italic px-2"
            >{{ STATUS_LABELS[data.status] }}</span>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Add voucher dialog — traditional Chinese format -->
    <Dialog v-model:visible="showAddDialog" :style="{ width: '1050px' }" @update:visible="resetForm()">
      <template #header>
        <div class="voucher-form-title">记 账 凭 证</div>
      </template>
      <div class="voucher-form">
        <!-- Meta row: company(left) date(center) voucher_no(right) all on same line -->
        <div class="voucher-meta">
          <div class="meta-left">{{ companyName }}</div>
          <div class="meta-center">{{ voucherForm.date || '____年__月__日' }}</div>
          <div class="meta-right">{{ voucherNoPreview }}</div>
        </div>

        <!-- Summary + voucher type row -->
        <div class="voucher-meta2">
          <div class="meta-item">
            凭证字：
            <Dropdown
              v-model="voucherForm.voucher_type"
              :options="TYPE_OPTIONS.filter(o => o.value)"
              option-label="label"
              option-value="value"
              class="meta-dropdown"
            />
          </div>
          <div class="meta-item meta-summary">
            {{ t('accounting.vouchers_page.summary') }}：<InputText v-model="voucherForm.summary" class="flex-1" placeholder="请输入凭证摘要" />
          </div>
          <div class="meta-item">
            {{ t('accounting.vouchers_page.voucherDate') }}：<InputText v-model="voucherForm.date" type="date" class="meta-input-date" />
          </div>
        </div>

        <!-- 6-column entry table -->
        <table class="voucher-table">
          <thead>
            <tr>
              <th class="col-code">科目编码</th>
              <th class="col-l1">一级科目</th>
              <th class="col-l2">明细科目</th>
              <th class="col-amount">{{ t('accounting.vouchers_page.entry_debit') }}</th>
              <th class="col-amount">{{ t('accounting.vouchers_page.entry_credit') }}</th>
              <th class="col-remark">{{ t('common.remark') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(entry, idx) in voucherForm.entries"
              :key="idx"
              :class="{ 'row-selected': selectedEntryIdx === idx }"
              @click="selectedEntryIdx = idx"
            >
              <td class="col-code">
                <Dropdown
                  v-model="entry.account_code"
                  :options="groupedAccounts"
                  optionGroupLabel="label"
                  optionGroupChildren="accounts"
                  option-label="display"
                  option-value="code"
                  placeholder="选择科目"
                  :filter="true"
                  class="w-full"
                  panel-class="text-sm"
                />
              </td>
              <td class="col-l1 readonly-cell">{{ getLevel1Name(entry.account_code) }}</td>
              <td class="col-l2 readonly-cell">{{ getDetailName(entry.account_code) }}</td>
              <td class="col-amount">
                <InputText
                  :model-value="entry.debit ? String(entry.debit) : ''"
                  @update:model-value="entry.debit = Number($event) || 0"
                  type="number"
                  placeholder="0.00"
                  class="amount-input"
                />
              </td>
              <td class="col-amount">
                <InputText
                  :model-value="entry.credit ? String(entry.credit) : ''"
                  @update:model-value="entry.credit = Number($event) || 0"
                  type="number"
                  placeholder="0.00"
                  class="amount-input"
                />
              </td>
              <td class="col-remark">
                <InputText v-model="entry.description" :placeholder="t('common.remark')" class="w-full" />
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="3" class="text-center font-semibold">{{ t('common.total') }}</td>
              <td class="col-amount total-value">{{ totalDebit.toFixed(2) }}</td>
              <td class="col-amount total-value">{{ totalCredit.toFixed(2) }}</td>
              <td class="text-center">
                <Tag v-if="balanced" value="借贷平衡" severity="success" />
                <Tag v-else value="不平衡" severity="danger" />
              </td>
            </tr>
          </tfoot>
        </table>

        <!-- Aux核算 panel -->
        <div v-if="selectedEntryAux" class="aux-panel">
          <div class="aux-title">辅助核算 — 第 {{ selectedEntryIdx + 1 }} 行</div>
          <div class="flex gap-3 flex-wrap">
            <div v-if="selectedEntryAux.dept" class="aux-field">
              <span class="aux-label">部门</span>
              <Dropdown
                v-model="voucherForm.entries[selectedEntryIdx].department_id"
                :options="departments"
                option-label="name"
                option-value="id"
                placeholder="选择部门"
                class="w-36"
              />
            </div>
            <div v-if="selectedEntryAux.person" class="aux-field">
              <span class="aux-label">个人</span>
              <Dropdown
                v-model="voucherForm.entries[selectedEntryIdx].person_id"
                :options="getPersonsForEntry(voucherForm.entries[selectedEntryIdx])"
                option-label="name"
                option-value="id"
                placeholder="选择个人"
                class="w-32"
              />
            </div>
            <div v-if="selectedEntryAux.counterparty" class="aux-field">
              <span class="aux-label">{{ t('accounting.vouchers_page.entry_counterparty') }}</span>
              <Dropdown
                v-model="voucherForm.entries[selectedEntryIdx].counterparty_id"
                :options="counterparties"
                option-label="name"
                option-value="id"
                placeholder="选择单位"
                class="w-44"
              />
            </div>
            <div v-if="selectedEntryAux.project" class="aux-field">
              <span class="aux-label">{{ t('accounting.vouchers_page.entry_project') }}</span>
              <Dropdown
                v-model="voucherForm.entries[selectedEntryIdx].project_id"
                :options="projects"
                option-label="name"
                option-value="id"
                placeholder="选择项目"
                class="w-40"
              />
            </div>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="voucher-actions">
          <Button label="+ 添加行" icon="pi pi-plus" text size="small" @click="addEntry(voucherForm)" />
          <div class="flex gap-2">
            <Button
              label="删除选中行"
              icon="pi pi-minus"
              text
              severity="danger"
              size="small"
              @click="removeEntry(voucherForm, selectedEntryIdx)"
              :disabled="voucherForm.entries.length <= 1"
            />
            <Button
              label="保存凭证"
              icon="pi pi-check"
              @click="handleCreate"
              :disabled="!balanced || saving"
              :loading="saving"
            />
          </div>
        </div>

        <p v-if="errorMsg" class="text-red-700 text-sm mt-2 text-center">{{ errorMsg }}</p>
      </div>
    </Dialog>

    <!-- Edit voucher dialog — same format as add -->
    <Dialog v-model:visible="showEditDialog" :style="{ width: '1050px' }">
      <template #header>
        <div class="voucher-form-title">记 账 凭 证</div>
      </template>
      <div class="voucher-form">
        <!-- Meta row -->
        <div class="voucher-meta">
          <div class="meta-left">{{ companyName }}</div>
          <div class="meta-center">{{ editForm.date || '____年__月__日' }}</div>
          <div class="meta-right">{{ editTarget?.voucher_no || '字第____号' }}</div>
        </div>

        <!-- Summary row -->
        <div class="voucher-meta2">
          <div class="meta-item">
            凭证字：
            <Dropdown
              v-model="editForm.voucher_type"
              :options="TYPE_OPTIONS.filter(o => o.value)"
              option-label="label"
              option-value="value"
              class="meta-dropdown"
            />
          </div>
          <div class="meta-item meta-summary">
            {{ t('accounting.vouchers_page.summary') }}：<InputText v-model="editForm.summary" class="flex-1" placeholder="请输入凭证摘要" />
          </div>
          <div class="meta-item">{{ t('accounting.vouchers_page.voucherDate') }}：<InputText v-model="editForm.date" type="date" class="meta-input-date" /></div>
        </div>

        <!-- 6-column entry table -->
        <table class="voucher-table">
          <thead>
            <tr>
              <th class="col-code">科目编码</th>
              <th class="col-l1">一级科目</th>
              <th class="col-l2">明细科目</th>
              <th class="col-amount">{{ t('accounting.vouchers_page.entry_debit') }}</th>
              <th class="col-amount">{{ t('accounting.vouchers_page.entry_credit') }}</th>
              <th class="col-remark">{{ t('common.remark') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(entry, idx) in editForm.entries"
              :key="idx"
              :class="{ 'row-selected': selectedEditEntryIdx === idx }"
              @click="selectedEditEntryIdx = idx"
            >
              <td class="col-code">
                <Dropdown
                  v-model="entry.account_code"
                  :options="groupedAccounts"
                  optionGroupLabel="label"
                  optionGroupChildren="accounts"
                  option-label="display"
                  option-value="code"
                  placeholder="选择科目"
                  :filter="true"
                  class="w-full"
                />
              </td>
              <td class="col-l1 readonly-cell">{{ getLevel1Name(entry.account_code) }}</td>
              <td class="col-l2 readonly-cell">{{ getDetailName(entry.account_code) }}</td>
              <td class="col-amount">
                <InputText
                  :model-value="entry.debit ? String(entry.debit) : ''"
                  @update:model-value="entry.debit = Number($event) || 0"
                  type="number"
                  placeholder="0.00"
                  class="amount-input"
                />
              </td>
              <td class="col-amount">
                <InputText
                  :model-value="entry.credit ? String(entry.credit) : ''"
                  @update:model-value="entry.credit = Number($event) || 0"
                  type="number"
                  placeholder="0.00"
                  class="amount-input"
                />
              </td>
              <td class="col-remark">
                <InputText v-model="entry.description" :placeholder="t('common.remark')" class="w-full" />
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="3" class="text-center font-semibold">{{ t('common.total') }}</td>
              <td class="col-amount total-value">{{ editDebit.toFixed(2) }}</td>
              <td class="col-amount total-value">{{ editCredit.toFixed(2) }}</td>
              <td class="text-center">
                <Tag v-if="editBalanced" value="借贷平衡" severity="success" />
                <Tag v-else value="不平衡" severity="danger" />
              </td>
            </tr>
          </tfoot>
        </table>

        <!-- Aux panel for edit -->
        <div v-if="editSelectedAux" class="aux-panel">
          <div class="aux-title">辅助核算 — 第 {{ selectedEditEntryIdx + 1 }} 行</div>
          <div class="flex gap-3 flex-wrap">
            <div v-if="editSelectedAux.dept" class="aux-field">
              <span class="aux-label">部门</span>
              <Dropdown
                v-model="editForm.entries[selectedEditEntryIdx].department_id"
                :options="departments"
                option-label="name"
                option-value="id"
                placeholder="选择部门"
                class="w-36"
              />
            </div>
            <div v-if="editSelectedAux.person" class="aux-field">
              <span class="aux-label">个人</span>
              <Dropdown
                v-model="editForm.entries[selectedEditEntryIdx].person_id"
                :options="getPersonsForEntry(editForm.entries[selectedEditEntryIdx])"
                option-label="name"
                option-value="id"
                placeholder="选择个人"
                class="w-32"
              />
            </div>
            <div v-if="editSelectedAux.counterparty" class="aux-field">
              <span class="aux-label">{{ t('accounting.vouchers_page.entry_counterparty') }}</span>
              <Dropdown
                v-model="editForm.entries[selectedEditEntryIdx].counterparty_id"
                :options="counterparties"
                option-label="name"
                option-value="id"
                placeholder="选择单位"
                class="w-44"
              />
            </div>
            <div v-if="editSelectedAux.project" class="aux-field">
              <span class="aux-label">{{ t('accounting.vouchers_page.entry_project') }}</span>
              <Dropdown
                v-model="editForm.entries[selectedEditEntryIdx].project_id"
                :options="projects"
                option-label="name"
                option-value="id"
                placeholder="选择项目"
                class="w-40"
              />
            </div>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="voucher-actions">
          <Button label="+ 添加行" icon="pi pi-plus" text size="small" @click="addEntry(editForm)" />
          <div class="flex gap-2">
            <Button
              label="删除选中行"
              icon="pi pi-minus"
              text
              severity="danger"
              size="small"
              @click="removeEntry(editForm, selectedEditEntryIdx)"
              :disabled="editForm.entries.length <= 1"
            />
            <Button
              label="保存修改"
              icon="pi pi-check"
              @click="handleEdit"
              :disabled="!editBalanced || saving"
              :loading="saving"
            />
          </div>
        </div>

        <p v-if="errorMsg" class="text-red-700 text-sm mt-2 text-center">{{ errorMsg }}</p>
      </div>
    </Dialog>

    <!-- Query dialog -->
    <Dialog v-model:visible="showQueryDialog" :header="t('accounting.vouchers_page.searchVoucher')" :style="{ width: '500px' }">
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">起始日期</label>
            <InputText v-model="queryFilters.start_date" type="date" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">截止日期</label>
            <InputText v-model="queryFilters.end_date" type="date" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">{{ t('accounting.vouchers_page.voucherNo') }}</label>
          <InputText v-model="queryFilters.voucher_no" placeholder="如：付字202601" class="w-full" />
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">{{ t('accounting.vouchers_page.voucherType') }}</label>
            <Dropdown
              v-model="queryFilters.voucher_type"
              :options="TYPE_OPTIONS"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">{{ t('accounting.vouchers_page.status') }}</label>
            <Dropdown
              v-model="queryFilters.status"
              :options="STATUS_OPTIONS"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </div>
        <div class="flex gap-2">
          <Button :label="t('common.search')" icon="pi pi-search" @click="handleQuery" />
          <Button :label="t('common.reset')" icon="pi pi-refresh" text @click="resetQuery" />
        </div>
      </div>
    </Dialog>

    <!-- Batch approve dialog -->
    <Dialog v-model:visible="showBatchApproveDialog" header="批量审核凭证" :style="{ width: '600px' }">
      <div class="flex flex-col gap-4 py-4">
        <p class="text-sm text-zinc-500">选择需要审核的草稿凭证：</p>
        <DataTable
          :value="draftVouchers"
          stripedRows
          selectionMode="checkbox"
          v-model:selection="selectedForApprove"
          class="shadow-sm"
          scrollHeight="300px"
          tableStyle="min-width: auto"
        >
          <Column selectionMode="multiple" style="width: 3rem" />
          <Column field="voucher_no" :header="t('accounting.vouchers_page.voucherNo')" style="width: 140px" />
          <Column field="date" :header="t('accounting.vouchers_page.voucherDate')" style="width: 90px" />
          <Column field="summary" :header="t('accounting.vouchers_page.summary')" style="width: 200px" />
        </DataTable>
        <Button
          label="批量审核"
          icon="pi pi-check"
          @click="handleBatchApprove"
          :disabled="!selectedForApprove.length"
        />
      </div>
    </Dialog>

    <!-- Reverse dialog -->
    <Dialog v-model:visible="showReverseDialog" header="反记账" :style="{ width: '450px' }">
      <div class="flex flex-col gap-4 py-4">
        <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">反记账原因（必填）</label>
        <Textarea v-model="reverseReason" rows="3" class="w-full" :placeholder="t('accounting.vouchers_page.reverseReasonPlaceholder')" />
        <Button
          label="确认反记账"
          icon="pi pi-exclamation-triangle"
          severity="danger"
          @click="handleReverse"
          :disabled="!reverseReason"
        />
      </div>
    </Dialog>

    <!-- 凭证详情查看弹窗 -->
    <Dialog v-model:visible="showDetailDialog" header="凭证详情" :style="{ width: '900px' }" :modal="true">
      <div v-if="detailVoucher" class="text-sm">
        <div class="grid grid-cols-4 gap-3 mb-4 p-3 bg-stone-50 rounded">
          <div><span class="text-zinc-500">凭证号</span><div class="font-medium">{{ detailVoucher.voucher_no }}</div></div>
          <div><span class="text-zinc-500">日期</span><div class="font-medium">{{ detailVoucher.date }}</div></div>
          <div><span class="text-zinc-500">凭证类型</span><div class="font-medium">{{ TYPE_LABELS[detailVoucher.voucher_type] || detailVoucher.voucher_type }}</div></div>
          <div><span class="text-zinc-500">状态</span><div><Tag :value="STATUS_LABELS[detailVoucher.status]" :severity="detailVoucher.status==='posted'?'success':detailVoucher.status==='approved'?'info':'warning'" /></div></div>
        </div>
        <div class="mb-4">
          <span class="text-zinc-500">摘要</span>
          <div class="font-medium">{{ detailVoucher.summary }}</div>
        </div>
        <DataTable :value="detailVoucher.entries || []" size="small" stripedRows class="text-sm">
          <Column header="科目代码" style="width: 110px">
            <template #body="{ data }">{{ data.account_code }}</template>
          </Column>
          <Column header="科目名称" style="width: 200px">
            <template #body="{ data }">{{ getAccountName(data.account_code) }}</template>
          </Column>
          <Column header="借方" style="width: 120px">
            <template #body="{ data }">{{ data.debit ? Number(data.debit).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '' }}</template>
          </Column>
          <Column header="贷方" style="width: 120px">
            <template #body="{ data }">{{ data.credit ? Number(data.credit).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : '' }}</template>
          </Column>
          <Column header="摘要" style="min-width: 200px">
            <template #body="{ data }">{{ data.description || '' }}</template>
          </Column>
        </DataTable>
        <div class="flex justify-between mt-3 p-2 bg-stone-50 rounded font-medium">
          <span>合计</span>
          <span>借: {{ totalDetailDebit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }} &nbsp; 贷: {{ totalDetailCredit.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
        </div>
        <!-- Detail action buttons -->
        <div class="flex gap-2 mt-4 justify-end">
          <Button
            v-if="detailVoucher.status === 'draft'"
            :label="t('common.edit')"
            severity="secondary"
            size="small"
            @click="showDetailDialog = false; openEdit(detailVoucher)"
          />
          <Button
            v-if="detailVoucher.status === 'draft'"
            :label="t('accounting.vouchers_page.approveVoucher')"
            severity="info"
            size="small"
            @click="handleApprove(detailVoucher.id)"
          />
          <Button
            v-if="detailVoucher.status === 'approved'"
            :label="t('accounting.vouchers_page.unapproveVoucher')"
            severity="warning"
            size="small"
            @click="handleUnapprove(detailVoucher.id)"
          />
          <Button
            v-if="detailVoucher.status === 'draft' || detailVoucher.status === 'approved'"
            :label="t('accounting.vouchers_page.postVoucher')"
            severity="success"
            size="small"
            @click="handlePost(detailVoucher.id)"
          />
          <Button
            v-if="detailVoucher.status === 'posted'"
            :label="t('accounting.vouchers_page.unpostVoucher')"
            severity="warning"
            size="small"
            @click="handleUnpost(detailVoucher.id)"
          />
          <Button
            v-if="detailVoucher.status === 'reversed'"
            :label="t('accounting.vouchers_page.unreverseVoucher')"
            severity="warning"
            size="small"
            @click="handleUnreverse(detailVoucher.id)"
          />
          <Button
            v-if="detailVoucher.status === 'posted'"
            :label="t('accounting.vouchers_page.reverseVoucher')"
            severity="danger"
            size="small"
            @click="reverseTarget = detailVoucher.id; reverseReason = ''; showDetailDialog = false; showReverseDialog = true"
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
/* === Voucher traditional form styles === */
.voucher-form {
  font-size: 11pt;
}

.voucher-form-title {
  text-align: center;
  font-size: 16pt;
  font-weight: bold;
  letter-spacing: 0.5em;
}

.voucher-form-company {
  text-align: center;
  font-size: 10pt;
  color: #555;
  margin-bottom: 0.75rem;
}

/* Meta row: left / center / right */
.voucher-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #999;
  font-size: 10pt;
}
.meta-left {
  text-align: left;
  flex: 1;
}
.meta-center {
  text-align: center;
  flex: 1;
  font-size: 11pt;
}
.meta-right {
  text-align: right;
  flex: 1;
}

/* Second meta row */
.voucher-meta2 {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.75rem;
  font-size: 10pt;
}
.voucher-meta2 .meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.voucher-meta2 .meta-summary {
  flex: 1;
}
.voucher-meta2 .meta-input-date {
  width: 140px;
}
.voucher-meta2 .meta-dropdown {
  width: 80px;
}

/* 6-column table */
.voucher-table {
  width: 100%;
  border-collapse: collapse;
  border: 1.5px solid #333;
  font-size: 10pt;
  table-layout: fixed;
}

.voucher-table th,
.voucher-table td {
  border: 0.5px solid #888;
  padding: 4px 5px;
  vertical-align: middle;
}

.voucher-table thead th {
  background: #f0f0f0;
  font-weight: 600;
  text-align: center;
  font-size: 9.5pt;
  padding: 6px 4px;
}

.col-code {
  width: 12%;
}
.col-l1 {
  width: 13%;
  text-align: center;
}
.col-l2 {
  width: 13%;
  text-align: center;
}
.col-amount {
  width: 14%;
  text-align: right;
}
.col-remark {
  width: 20%;
}

.readonly-cell {
  color: #666;
  font-size: 9pt;
  word-break: break-all;
}

.amount-input {
  width: 100%;
  text-align: right;
  font-family: 'Courier New', monospace;
}

.voucher-table .row-selected {
  background: #e8f0fe;
  outline: 1px solid #93c5fd;
}

.voucher-table .total-row td {
  font-weight: bold;
  border-top: 1.5px solid #333;
  background: #fafafa;
  text-align: center;
}
.voucher-table .total-row .total-value {
  text-align: right;
  font-family: 'Courier New', monospace;
}

/* Aux核算 panel */
.aux-panel {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #d6d3d1;
  border-radius: 4px;
  background: #fafaf9;
}
.aux-title {
  font-size: 9.5pt;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #555;
}
.aux-field {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.aux-label {
  font-size: 9pt;
  color: #888;
  min-width: 3em;
}

/* Action buttons */
.voucher-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.75rem;
}

/* === Print styles === */
@media print {
  @page {
    size: A4 portrait;
    margin: 10mm;
  }

  body * {
    visibility: hidden;
  }

  .p-dialog,
  .p-dialog *,
  .voucher-form,
  .voucher-form * {
    visibility: visible;
  }

  .p-dialog {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    box-shadow: none !important;
    border: none !important;
  }

  .p-dialog-header,
  .p-dialog-footer,
  .voucher-actions,
  .aux-panel,
  .p-dropdown,
  .p-button,
  .meta-dropdown,
  .meta-input-date,
  .amount-input,
  input,
  select {
    display: none !important;
  }

  .voucher-form-title {
    font-size: 13pt;
  }
  .voucher-form-company {
    color: #000;
  }
  .voucher-meta,
  .voucher-meta2 {
    border-bottom-color: #000;
  }
  .voucher-table {
    border-color: #000;
    font-size: 8.5pt;
  }
  .voucher-table th,
  .voucher-table td {
    border-color: #000;
    padding: 2px 4px;
  }

  .readonly-cell {
    color: #000;
  }
}
</style>
