<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useConfirm } from 'primevue/useconfirm'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import DatePicker from 'primevue/datepicker'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Toolbar from 'primevue/toolbar'

import {
  listTenderProjects,
  getTenderOptions,
  createTenderProject,
  updateTenderProject,
  deleteTenderProject,
  reviewTenderProject,
  approveTenderProject,
  bypassTenderProject,
} from '../../api/bids'
import api from '../../api'

const route = useRoute()
const confirm = useConfirm()

// ── 模式检测 ──
const modeLabels: Record<string, string> = {
  projects: '招标立项',
  documents: '招标文件',
  openings: '开标管理',
  evaluations: '评标管理',
  awards: '定标管理',
}

const mode = computed(() => {
  const seg = route.path.split('/').pop() || 'projects'
  return seg
})

const pageTitle = computed(() => modeLabels[mode.value] || '招标项目')

// ── 状态常量 ──
const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已公告', value: 'announced' },
  { label: '开标中', value: 'opening' },
  { label: '评标中', value: 'evaluating' },
  { label: '已定标', value: 'awarded' },
  { label: '已关闭', value: 'closed' },
  { label: '已取消', value: 'cancelled' },
]

const statusLabels: Record<string, string> = Object.fromEntries(statusOptions.map(o => [o.value, o.label]))
const statusSeverity: Record<string, string> = {
  draft: 'info',
  announced: 'warn',
  opening: 'warn',
  evaluating: 'warn',
  awarded: 'success',
  closed: 'secondary',
  cancelled: 'danger',
}

const tenderTypeOptions = [
  { label: '公开招标', value: '公开招标' },
  { label: '邀请招标', value: '邀请招标' },
  { label: '竞争性谈判', value: '竞争性谈判' },
  { label: '询价', value: '询价' },
  { label: '单一来源', value: '单一来源' },
]

const procurementCategoryOptions = [
  { label: '货物', value: '货物' },
  { label: '工程', value: '工程' },
  { label: '服务', value: '服务' },
]

const evaluationMethodOptions = [
  { label: '综合评分法', value: '综合评分法' },
  { label: '最低价法', value: '最低价法' },
  { label: '性价比法', value: '性价比法' },
]

// ── 数据状态 ──
const items = ref<any[]>([])
const loading = ref(false)
const departments = ref<any[]>([])

// 筛选
const fTenderType = ref<string[]>([])
const fProcurementCategory = ref<string[]>([])
const fDepartment = ref<string[]>([])
const fStatus = ref<string>()
const fSearch = ref('')

// 对话框
const showDialog = ref(false)
const isEdit = ref(false)
const form = ref<Record<string, any>>({})
const submitting = ref(false)

// ── 默认表单 ──
function emptyForm(): Record<string, any> {
  const now = new Date().toISOString().slice(0, 10)
  return {
    company_id: Number(localStorage.getItem('company_id') || '1'),
    project_no: `ZB-${now.replace(/-/g, '')}-`,
    project_name: '',
    tender_type: '公开招标',
    procurement_category: '服务',
    department_id: null,
    owner_id: null,
    estimated_amount: 0,
    currency: 'CNY',
    announcement_date: null,
    bid_deadline: null,
    opening_date: null,
    opening_location: '',
    evaluation_method: '综合评分法',
    evaluation_summary: '',
    status: 'draft',
    winner_name: '',
    winner_amount: null,
    award_date: null,
    result_summary: '',
    tender_doc_path: '',
    bid_opening_record: '',
    notes: '',
  }
}

// ── 权限 ──
const userRole = computed(() => localStorage.getItem('role') || '')
const isPrivileged = computed(() => ['finance_manager', 'finance_director', 'super_admin'].includes(userRole.value))
const canBypass = computed(() => ['super_admin', 'finance_director'].includes(userRole.value))

const bypassDialog = ref(false)
const bypassReason = ref('')
const currentProjectId = ref<number | null>(null)

const openBypassProject = (id: number) => {
  currentProjectId.value = id
  bypassReason.value = ''
  bypassDialog.value = true
}

const doBypassProject = async () => {
  try {
    await bypassTenderProject(currentProjectId.value!, bypassReason.value)
    bypassDialog.value = false
    load()
  } catch (e: any) {
    alert('操作失败: ' + (e.response?.data?.detail || e.message))
  }
}

// ── 数据加载 ──
async function load() {
  loading.value = true
  try {
    const r = await listTenderProjects({
      company_id: Number(localStorage.getItem('company_id') || '1'),
      tender_type: fTenderType.value.length > 0 ? fTenderType.value.join(',') : undefined,
      procurement_category: fProcurementCategory.value.length > 0 ? fProcurementCategory.value.join(',') : undefined,
      department_id: fDepartment.value.length === 1 ? Number(fDepartment.value[0]) : undefined,
      status: fStatus.value,
      search: fSearch.value || undefined,
    })
    items.value = r.data
  } finally {
    loading.value = false
  }
}

async function loadRefs() {
  try {
    const [deptRes] = await Promise.all([
      api.get('/departments', { params: { company_id: Number(localStorage.getItem('company_id') || '1') } }),
    ])
    departments.value = deptRes.data.map((d: any) => ({ label: d.name, value: d.id }))
  } catch {
    /* ignore */
  }
}

// ── CRUD ──
function openCreate() {
  isEdit.value = false
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row: any) {
  isEdit.value = true
  form.value = { ...row }
  showDialog.value = true
}

async function save() {
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateTenderProject(form.value.id, form.value)
    } else {
      await createTenderProject(form.value)
    }
    showDialog.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

function remove(id: number) {
  confirm.require({
    message: '确认删除该招标项目？',
    header: '确认删除',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      await deleteTenderProject(id)
      await load()
    },
  })
}

// ── 审批流程 ──
async function doReview(id: number) {
  await reviewTenderProject(id)
  await load()
}

async function doApprove(id: number) {
  await approveTenderProject(id)
  await load()
}

// ── 生命周期 ──
onMounted(() => {
  loadRefs()
  load()
})
</script>

<template>
  <div class="p-4">
    <!-- 标题栏 -->
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold">{{ pageTitle }}</h1>
      <Button v-if="mode === 'projects'" label="新建招标项目" icon="pi pi-plus" @click="openCreate" />
    </div>

    <!-- 筛选栏 -->
    <Toolbar class="mb-4">
      <template #start>
        <div class="flex flex-wrap gap-3">
          <MultiSelect v-model="fTenderType" :options="tenderTypeOptions" placeholder="招标类型" class="w-40" />
          <MultiSelect
            v-model="fProcurementCategory"
            :options="procurementCategoryOptions"
            placeholder="采购类别"
            class="w-36"
          />
          <MultiSelect v-model="fDepartment" :options="departments" placeholder="部门" class="w-36" />
          <Dropdown v-model="fStatus" :options="statusOptions" placeholder="状态" class="w-32" showClear />
          <InputText v-model="fSearch" placeholder="搜索编号/名称" class="w-48" @keyup.enter="load" />
          <Button icon="pi pi-search" label="查询" @click="load" />
        </div>
      </template>
    </Toolbar>

    <!-- 数据表格 -->
    <DataTable
      :value="items"
      :loading="loading"
      stripedRows
      paginator
      :rows="15"
      :rowsPerPageOptions="[10, 15, 25, 50]"
      class="text-sm"
    >
      <Column field="project_no" header="招标编号" style="min-width: 140px" />
      <Column field="project_name" header="项目名称" style="min-width: 200px" />
      <Column field="tender_type" header="招标类型" style="min-width: 100px" />
      <Column field="procurement_category" header="采购类别" style="min-width: 80px" />
      <Column field="estimated_amount" header="预算金额" style="min-width: 100px">
        <template #body="{ data }">{{ data.estimated_amount?.toLocaleString() }}</template>
      </Column>
      <Column field="bid_deadline" header="投标截止" style="min-width: 100px" />
      <Column field="opening_date" header="开标日期" style="min-width: 100px" />
      <Column field="status" header="状态" style="min-width: 90px">
        <template #body="{ data }">
          <Tag :value="statusLabels[data.status]" :severity="statusSeverity[data.status]" />
        </template>
      </Column>
      <Column header="操作" style="min-width: 220px">
        <template #body="{ data }">
          <div class="flex gap-1 flex-wrap">
            <Button
              v-if="mode === 'projects'"
              icon="pi pi-pencil"
              size="small"
              severity="info"
              @click="openEdit(data)"
              v-tooltip.top="'编辑'"
            />
            <Button
              v-if="isPrivileged && !data.reviewer_id"
              icon="pi pi-check"
              size="small"
              severity="warn"
              @click="doReview(data.id)"
              v-tooltip.top="'审核'"
            />
            <Button
              v-if="isPrivileged && data.reviewer_id && data.status === 'draft'"
              icon="pi pi-check-circle"
              size="small"
              severity="success"
              @click="doApprove(data.id)"
              v-tooltip.top="'批准公告'"
            />
            <Button
              v-if="canBypass && data.status === 'draft'"
              icon="pi pi-forward"
              size="small"
              severity="warn"
              @click="openBypassProject(data.id)"
              v-tooltip.top="'强制跳过'"
            />
            <Button
              v-if="mode === 'projects'"
              icon="pi pi-trash"
              size="small"
              severity="danger"
              @click="remove(data.id)"
              v-tooltip.top="'删除'"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- 编辑/创建对话框 -->
    <Dialog
      v-model:visible="showDialog"
      :header="(isEdit ? '编辑' : '新建') + '招标项目'"
      :style="{ width: '800px' }"
      :modal="true"
      class="p-fluid"
    >
      <div class="grid grid-cols-2 gap-4" style="max-height: 60vh; overflow-y: auto; padding-right: 4px">
        <!-- 基本信息 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">基本信息</div>
        <div>
          <label class="block text-sm font-medium mb-1">项目名称 *</label>
          <InputText v-model="form.project_name" required />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">招标编号</label>
          <InputText v-model="form.project_no" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">招标类型</label>
          <Dropdown v-model="form.tender_type" :options="tenderTypeOptions" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">采购类别</label>
          <Dropdown v-model="form.procurement_category" :options="procurementCategoryOptions" />
        </div>

        <!-- 金额 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">金额信息</div>
        <div>
          <label class="block text-sm font-medium mb-1">预算金额</label>
          <InputNumber v-model="form.estimated_amount" mode="currency" currency="CNY" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">币种</label>
          <InputText v-model="form.currency" />
        </div>

        <!-- 日期 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">时间节点</div>
        <div>
          <label class="block text-sm font-medium mb-1">公告日期</label>
          <DatePicker v-model="form.announcement_date" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">投标截止日期</label>
          <DatePicker v-model="form.bid_deadline" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">开标日期</label>
          <DatePicker v-model="form.opening_date" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">开标地点</label>
          <InputText v-model="form.opening_location" />
        </div>

        <!-- 评标 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">评标信息</div>
        <div>
          <label class="block text-sm font-medium mb-1">评标方法</label>
          <Dropdown v-model="form.evaluation_method" :options="evaluationMethodOptions" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">评标总结</label>
          <Textarea v-model="form.evaluation_summary" rows="3" />
        </div>

        <!-- 定标 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">定标结果</div>
        <div>
          <label class="block text-sm font-medium mb-1">中标单位</label>
          <InputText v-model="form.winner_name" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">中标金额</label>
          <InputNumber v-model="form.winner_amount" mode="currency" currency="CNY" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">定标日期</label>
          <DatePicker v-model="form.award_date" class="w-full" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">定标结果摘要</label>
          <Textarea v-model="form.result_summary" rows="3" />
        </div>

        <!-- 文件 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">文件与记录</div>
        <div>
          <label class="block text-sm font-medium mb-1">招标文件路径</label>
          <InputText v-model="form.tender_doc_path" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">开标记录</label>
          <Textarea v-model="form.bid_opening_record" rows="3" />
        </div>

        <!-- 管理 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">管理</div>
        <div>
          <label class="block text-sm font-medium mb-1">负责部门</label>
          <Dropdown v-model="form.department_id" :options="departments" showClear placeholder="选择部门" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">状态</label>
          <Dropdown v-model="form.status" :options="statusOptions" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">备注</label>
          <Textarea v-model="form.notes" rows="2" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" icon="pi pi-times" severity="secondary" @click="showDialog = false" />
        <Button label="保存" icon="pi pi-check" :loading="submitting" @click="save" />
      </template>
    </Dialog>

    <!-- Bypass dialog -->
    <Dialog v-model:visible="bypassDialog" header="强制跳过审批" :modal="true" :style="{ width: '28rem' }">
      <div class="flex flex-col gap-3">
        <p class="text-sm text-stone-600">您正在强制跳过招标项目审批，此操作将记录到审计日志。</p>
        <label class="form-label">跳过原因（必填）</label>
        <Textarea v-model="bypassReason" class="w-full" rows="3" placeholder="请填写强制跳过原因" />
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="bypassDialog = false" />
        <Button label="确认跳过" severity="warn" :disabled="!bypassReason.trim()" @click="doBypassProject" />
      </template>
    </Dialog>
  </div>
</template>
