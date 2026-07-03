<script setup lang="ts">
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import DatePicker from 'primevue/datepicker'
import {
  type BoardFilingData,
  type BoardFilingCreateData,
  type BoardFilingUpdateData,
  listFilings,
  createFiling,
  updateFiling,
  deleteFiling,
} from '@/api/board'

const route = useRoute()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

// Determine doc_type from route
const routeDocType = computed(() => {
  const p = route.path
  if (p.includes('/board/filings')) return 'filing'
  if (p.includes('/board/approvals')) return 'approval'
  if (p.includes('/board/meetings')) return 'meeting'
  if (p.includes('/board/archives')) return 'archive'
  if (p.includes('/board/contacts')) return 'contact'
  return 'filing'
})

const pageConfig = computed(() => {
  const m: Record<
    string,
    {
      title: string
      statuses: { label: string; value: string; severity?: string }[]
      subtypes: { label: string; value: string }[]
    }
  > = {
    filing: {
      title: '合规报送管理',
      statuses: [
        { label: '待提交', value: '待提交', severity: 'warn' },
        { label: '已提交', value: '已提交', severity: 'info' },
        { label: '已反馈', value: '已反馈', severity: 'success' },
        { label: '已逾期', value: '已逾期', severity: 'danger' },
        { label: '已完成', value: '已完成', severity: 'success' },
      ],
      subtypes: [
        { label: '证监会/局规定文件', value: 'csrc' },
        { label: '交易所规定文件', value: 'exchange' },
        { label: '股东大会法律文件', value: 'shareholder' },
        { label: '财务部门报备文件', value: 'finance' },
      ],
    },
    approval: {
      title: '内部报批流程',
      statuses: [
        { label: '草稿', value: '草稿' },
        { label: '部门审核', value: '部门审核' },
        { label: '董秘审核', value: '董秘审核' },
        { label: '董事长审批', value: '董事长审批' },
        { label: '已完成', value: '已完成', severity: 'success' },
      ],
      subtypes: [
        { label: '决议草案', value: 'resolution' },
        { label: '信息披露文件', value: 'disclosure' },
        { label: '法律文件', value: 'legal' },
        { label: '分红方案', value: 'dividend' },
        { label: '章程修订', value: 'charter_amendment' },
        { label: '其他报批', value: 'other' },
      ],
    },
    meeting: {
      title: '三会决议管理',
      statuses: [
        { label: '待提交', value: '待提交' },
        { label: '已提交', value: '已提交' },
        { label: '已反馈', value: '已反馈' },
        { label: '已逾期', value: '已逾期', severity: 'danger' },
        { label: '已完成', value: '已完成', severity: 'success' },
      ],
      subtypes: [
        { label: '股东大会', value: 'shareholder' },
        { label: '董事会', value: 'board' },
        { label: '监事会', value: 'supervisory' },
      ],
    },
    archive: {
      title: '档案管理',
      statuses: [
        { label: '有效', value: '有效', severity: 'success' },
        { label: '已归档', value: '已归档', severity: 'info' },
        { label: '已过期', value: '已过期', severity: 'danger' },
      ],
      subtypes: [
        { label: '公司章程', value: 'charter' },
        { label: '协议合同', value: 'agreement' },
        { label: '投资文件', value: 'investment' },
        { label: '分红方案', value: 'dividend' },
        { label: '法律文件', value: 'legal' },
        { label: '财务报告', value: 'financial_report' },
        { label: '其他档案', value: 'other' },
      ],
    },
    contact: {
      title: '对接联络日志',
      statuses: [
        { label: '待跟进', value: '待跟进' },
        { label: '已联系', value: '已联系' },
        { label: '已完成', value: '已完成', severity: 'success' },
      ],
      subtypes: [],
    },
  }
  return m[routeDocType.value] || m.filing
})

// 下拉选项 — 证监会机构
const csrcOrgs = [
  { label: '中国证监会', value: '中国证监会' },
  { label: '香港证监会', value: '香港证监会' },
  { label: '美国SEC', value: '美国SEC' },
  { label: '其他', value: '其他' },
]

// 下拉选项 — 交易所
const exchanges = [
  { label: '上海证券交易所', value: '上海证券交易所' },
  { label: '深圳证券交易所', value: '深圳证券交易所' },
  { label: '北京证券交易所', value: '北京证券交易所' },
  { label: '香港证券交易所', value: '香港证券交易所' },
  { label: '纽约证券交易所', value: '纽约证券交易所' },
  { label: 'Nasdaq', value: 'Nasdaq' },
  { label: '其他', value: '其他' },
]

const data = ref<BoardFilingData[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = reactive({
  company_id: companyId.value,
  doc_type: routeDocType.value,
  title: '',
  doc_subtype: '',
  target_org: '',
  deadline: null as Date | null,
  submit_date: null as Date | null,
  status: pageConfig.value.statuses[0]?.value || '待提交',
  approver: '',
  contact_person: '',
  contact_method: '',
  party_name: '',
  summary: '',
  content: '',
  file_path: '',
})

function fmtDate(d: Date | null): string {
  if (!d) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function parseDate(s: string | null | undefined): Date | null {
  if (!s) return null
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

async function load() {
  loading.value = true
  try {
    const res = await listFilings(companyId.value, routeDocType.value)
    data.value = res.data || []
  } catch {
    /* */
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingId.value = null
  form.company_id = companyId.value
  form.doc_type = routeDocType.value
  form.title = ''
  form.doc_subtype = ''
  form.target_org = ''
  form.deadline = null
  form.submit_date = null
  form.status = pageConfig.value.statuses[0]?.value || '待提交'
  form.approver = ''
  form.contact_person = ''
  form.contact_method = ''
  form.party_name = ''
  form.summary = ''
  form.content = ''
  form.file_path = ''
  showDialog.value = true
}

function openEdit(row: BoardFilingData) {
  editingId.value = row.id
  form.company_id = row.company_id
  form.doc_type = row.doc_type
  form.title = row.title
  form.doc_subtype = row.doc_subtype || ''
  form.target_org = row.target_org || ''
  form.deadline = parseDate(row.deadline)
  form.submit_date = parseDate(row.submit_date)
  form.status = row.status
  form.approver = row.approver || ''
  form.contact_person = row.contact_person || ''
  form.contact_method = row.contact_method || ''
  form.party_name = row.party_name || ''
  form.summary = row.summary || ''
  form.content = row.content || ''
  form.file_path = row.file_path || ''
  showDialog.value = true
}

async function save() {
  saving.value = true
  try {
    const payload: BoardFilingCreateData = {
      company_id: form.company_id,
      doc_type: form.doc_type,
      doc_subtype: form.doc_subtype || undefined,
      title: form.title,
      target_org: form.target_org || undefined,
      deadline: fmtDate(form.deadline) || undefined,
      submit_date: fmtDate(form.submit_date) || undefined,
      status: form.status,
      approver: form.approver || undefined,
      contact_person: form.contact_person || undefined,
      contact_method: form.contact_method || undefined,
      party_name: form.party_name || undefined,
      summary: form.summary || undefined,
      content: form.content || undefined,
      file_path: form.file_path || undefined,
    }
    if (editingId.value) {
      await updateFiling(editingId.value, payload as BoardFilingUpdateData)
    } else {
      await createFiling(payload)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  if (!confirm('确定删除此记录？')) return
  await deleteFiling(id)
  await load()
}

function statusSeverity(status: string) {
  const s = pageConfig.value.statuses.find(st => st.value === status)
  return (s?.severity as any) || 'info'
}

const approvalSteps = ['草稿', '部门审核', '董秘审核', '董事长审批', '已完成']
function approvalStepIndex(status: string) {
  return approvalSteps.indexOf(status)
}

watch(routeDocType, () => {
  form.doc_type = routeDocType.value
  form.status = pageConfig.value.statuses[0]?.value || '待提交'
  load()
})

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="page-header flex items-center justify-between">
      <h2>{{ pageConfig.title }}</h2>
      <Button label="新增" icon="pi pi-plus" size="small" @click="openAdd" />
    </div>

    <div class="form-card overflow-x-auto">
      <DataTable :value="data" :loading="loading" stripedRows class="text-xs" paginator :rows="15">
        <Column field="title" header="标题" style="min-width: 180px" />
        <Column field="doc_subtype" header="子类型" style="width: 130px">
          <template #body="{ data: row }">
            <span v-if="pageConfig.subtypes.length" class="text-stone-500">
              {{ pageConfig.subtypes.find(s => s.value === row.doc_subtype)?.label || row.doc_subtype }}
            </span>
            <span v-else class="text-stone-400">—</span>
          </template>
        </Column>
        <Column field="target_org" header="目标机构" style="width: 120px">
          <template #body="{ data: row }">{{ row.target_org || '—' }}</template>
        </Column>
        <Column field="deadline" header="截止日期" style="width: 100px">
          <template #body="{ data: row }">{{ row.deadline || '—' }}</template>
        </Column>
        <Column header="状态" style="width: 90px">
          <template #body="{ data: row }">
            <Tag :value="row.status" :severity="statusSeverity(row.status)" />
          </template>
        </Column>
        <Column v-if="routeDocType === 'approval'" header="审批进度" style="width: 200px">
          <template #body="{ data: row }">
            <div class="flex items-center gap-1">
              <template v-for="(step, idx) in approvalSteps" :key="step">
                <div
                  class="w-3 h-3 rounded-full border text-[0px]"
                  :class="
                    idx <= approvalStepIndex(row.status) ? 'bg-amber-500 border-amber-500' : 'bg-white border-stone-300'
                  "
                />
                <div
                  v-if="idx < approvalSteps.length - 1"
                  class="h-px flex-1"
                  :class="idx < approvalStepIndex(row.status) ? 'bg-amber-500' : 'bg-stone-200'"
                />
              </template>
            </div>
          </template>
        </Column>
        <Column header="操作" style="width: 110px">
          <template #body="{ data: row }">
            <Button label="编辑" text size="small" @click="openEdit(row)" />
            <Button label="删除" text severity="danger" size="small" @click="handleDelete(row.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Dialog -->
    <Dialog
      v-model:visible="showDialog"
      :header="editingId ? '编辑记录' : '新增记录'"
      :style="{ width: '620px' }"
      modal
    >
      <div class="flex flex-col gap-3 py-4 text-sm">
        <div>
          <label class="text-xs text-zinc-500 mb-1 block">标题 *</label>
          <InputText v-model="form.title" class="w-full" required />
        </div>

        <!-- Subtype dropdown (except for contact type) -->
        <div v-if="pageConfig.subtypes.length > 0">
          <label class="text-xs text-zinc-500 mb-1 block">类型</label>
          <Dropdown
            v-model="form.doc_subtype"
            :options="pageConfig.subtypes"
            option-label="label"
            option-value="value"
            class="w-full"
            placeholder="选择类型"
          />
        </div>

        <!-- Target org: csrc dropdown for filing->csrc -->
        <div v-if="form.doc_type === 'filing' && form.doc_subtype === 'csrc'">
          <label class="text-xs text-zinc-500 mb-1 block">证监会机构</label>
          <Dropdown
            v-model="form.target_org"
            :options="csrcOrgs"
            option-label="label"
            option-value="value"
            class="w-full"
            placeholder="选择证监会机构"
          />
        </div>

        <!-- Target org: exchange dropdown for filing->exchange -->
        <div v-if="form.doc_type === 'filing' && form.doc_subtype === 'exchange'">
          <label class="text-xs text-zinc-500 mb-1 block">交易所</label>
          <Dropdown
            v-model="form.target_org"
            :options="exchanges"
            option-label="label"
            option-value="value"
            class="w-full"
            placeholder="选择交易所"
          />
        </div>

        <!-- Target org: free text for others -->
        <div
          v-if="
            routeDocType !== 'contact' &&
            !(form.doc_type === 'filing' && (form.doc_subtype === 'csrc' || form.doc_subtype === 'exchange'))
          "
        >
          <label class="text-xs text-zinc-500 mb-1 block">目标机构</label>
          <InputText v-model="form.target_org" class="w-full" placeholder="例如：股东大会、财务部..." />
        </div>

        <!-- Contact-specific fields -->
        <template v-if="routeDocType === 'contact'">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">对方单位</label>
            <InputText v-model="form.party_name" class="w-full" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">联系人</label>
            <InputText v-model="form.contact_person" class="w-full" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">联系方式</label>
            <InputText v-model="form.contact_method" class="w-full" />
          </div>
        </template>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">截止日期</label>
            <DatePicker v-model="form.deadline" date-format="yy-mm-dd" class="w-full" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">实际日期</label>
            <DatePicker v-model="form.submit_date" date-format="yy-mm-dd" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">状态</label>
            <Dropdown
              v-model="form.status"
              :options="pageConfig.statuses"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
          <div v-if="routeDocType === 'approval'">
            <label class="text-xs text-zinc-500 mb-1 block">审批人</label>
            <InputText v-model="form.approver" class="w-full" placeholder="当前审批人" />
          </div>
        </div>

        <div>
          <label class="text-xs text-zinc-500 mb-1 block">摘要</label>
          <Textarea v-model="form.summary" rows="2" class="w-full" />
        </div>

        <div>
          <label class="text-xs text-zinc-500 mb-1 block">正文 (Markdown)</label>
          <Textarea v-model="form.content" rows="4" class="w-full" />
        </div>

        <div>
          <label class="text-xs text-zinc-500 mb-1 block">附件路径</label>
          <InputText v-model="form.file_path" class="w-full" placeholder="文件路径或链接" />
        </div>

        <Button label="保存" icon="pi pi-check" :loading="saving" @click="save" />
      </div>
    </Dialog>
  </div>
</template>
