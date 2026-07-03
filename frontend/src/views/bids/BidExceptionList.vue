<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useConfirm } from 'primevue/useconfirm'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import DatePicker from 'primevue/datepicker'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Toolbar from 'primevue/toolbar'

import {
  listExceptionEvents,
  getExceptionOptions,
  createExceptionEvent,
  updateExceptionEvent,
  deleteExceptionEvent,
  reviewExceptionEvent,
  approveExceptionEvent,
  rejectExceptionEvent,
  bypassExceptionEvent,
} from '../../api/bids'
import api from '../../api'

const route = useRoute()
const confirm = useConfirm()

// ── 模式检测：根据路由决定 target_type ──
const routeTargetType = computed(() => {
  if (route.path.includes('/tendering/')) return 'tender_project'
  if (route.path.includes('/bidding/')) return 'bid_submission'
  return 'tender_project'
})

const isTendering = computed(() => routeTargetType.value === 'tender_project')
const pageTitle = computed(() => (isTendering.value ? '招标例外事项' : '投标例外事项'))

// ── 常量 ──
const tenderExceptionTypeOptions = [
  { label: '流标', value: '流标' },
  { label: '废标', value: '废标' },
  { label: '终止招标', value: '终止招标' },
  { label: '变更采购方式', value: '变更采购方式' },
  { label: '紧急采购', value: '紧急采购' },
  { label: '其他', value: '其他' },
]

const bidExceptionTypeOptions = [
  { label: '弃标', value: '弃标' },
  { label: '被废标', value: '被废标' },
  { label: '异议申诉', value: '异议申诉' },
  { label: '保证金争议', value: '保证金争议' },
  { label: '中标后变更', value: '中标后变更' },
  { label: '其他', value: '其他' },
]

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已审核', value: 'reviewed' },
  { label: '已批准', value: 'approved' },
  { label: '已驳回', value: 'rejected' },
  { label: '已关闭', value: 'closed' },
]

const statusLabels: Record<string, string> = Object.fromEntries(statusOptions.map(o => [o.value, o.label]))
const statusSeverity: Record<string, string> = {
  draft: 'info',
  reviewed: 'warn',
  approved: 'success',
  rejected: 'danger',
  closed: 'secondary',
}

const exceptionTypeOptions = computed(() => (isTendering.value ? tenderExceptionTypeOptions : bidExceptionTypeOptions))

// ── 数据状态 ──
const items = ref<any[]>([])
const loading = ref(false)
const departments = ref<any[]>([])

const fExceptionType = ref<string>()
const fStatus = ref<string>()
const fSearch = ref('')

const showDialog = ref(false)
const isEdit = ref(false)
const form = ref<Record<string, any>>({})
const submitting = ref(false)

function emptyForm(): Record<string, any> {
  return {
    company_id: Number(localStorage.getItem('company_id') || '1'),
    target_type: routeTargetType.value,
    target_id: null,
    exception_type: '',
    title: '',
    reason: '',
    resolution: '',
    status: 'draft',
    department_id: null,
    owner_id: null,
    notes: '',
  }
}

// ── 权限 ──
const userRole = computed(() => localStorage.getItem('role') || '')
const isPrivileged = computed(() => ['finance_manager', 'finance_director', 'super_admin'].includes(userRole.value))
const canBypass = computed(() => ['super_admin', 'finance_director'].includes(userRole.value))

const bypassDialog = ref(false)
const bypassReason = ref('')
const currentExceptionId = ref<number | null>(null)

const openBypassException = (id: number) => {
  currentExceptionId.value = id
  bypassReason.value = ''
  bypassDialog.value = true
}

const doBypassException = async () => {
  try {
    await bypassExceptionEvent(currentExceptionId.value!, bypassReason.value)
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
    const r = await listExceptionEvents({
      company_id: Number(localStorage.getItem('company_id') || '1'),
      target_type: routeTargetType.value,
      exception_type: fExceptionType.value,
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
      await updateExceptionEvent(form.value.id, form.value)
    } else {
      await createExceptionEvent(form.value)
    }
    showDialog.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

function remove(id: number) {
  confirm.require({
    message: '确认删除该例外事项？',
    header: '确认删除',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      await deleteExceptionEvent(id)
      await load()
    },
  })
}

async function doReview(id: number) {
  await reviewExceptionEvent(id)
  await load()
}

async function doApprove(id: number) {
  confirm.require({
    message: '批准该例外事项将联动更新关联项目的状态，确认继续？',
    header: '确认批准',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      await approveExceptionEvent(id)
      await load()
    },
  })
}

async function doReject(id: number) {
  await rejectExceptionEvent(id)
  await load()
}

onMounted(() => {
  loadRefs()
  load()
})
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold">{{ pageTitle }}</h1>
      <Button label="新建例外事项" icon="pi pi-plus" @click="openCreate" />
    </div>

    <Toolbar class="mb-4">
      <template #start>
        <div class="flex flex-wrap gap-3">
          <Dropdown
            v-model="fExceptionType"
            :options="exceptionTypeOptions"
            placeholder="例外类型"
            class="w-36"
            showClear
          />
          <Dropdown v-model="fStatus" :options="statusOptions" placeholder="状态" class="w-32" showClear />
          <InputText v-model="fSearch" placeholder="搜索标题/事由" class="w-48" @keyup.enter="load" />
          <Button icon="pi pi-search" label="查询" @click="load" />
        </div>
      </template>
    </Toolbar>

    <DataTable
      :value="items"
      :loading="loading"
      stripedRows
      paginator
      :rows="15"
      :rowsPerPageOptions="[10, 15, 25, 50]"
      class="text-sm"
    >
      <Column field="exception_type" header="例外类型" style="min-width: 110px">
        <template #body="{ data }">
          <Tag :value="data.exception_type" severity="warn" />
        </template>
      </Column>
      <Column field="title" header="标题" style="min-width: 180px" />
      <Column field="target_id" header="关联项目ID" style="min-width: 90px" />
      <Column field="reason" header="事由" style="min-width: 200px">
        <template #body="{ data }">{{ (data.reason || '').slice(0, 60) }}</template>
      </Column>
      <Column field="resolution" header="处理结果" style="min-width: 150px">
        <template #body="{ data }">{{ (data.resolution || '').slice(0, 40) || '-' }}</template>
      </Column>
      <Column field="status" header="状态" style="min-width: 90px">
        <template #body="{ data }">
          <Tag :value="statusLabels[data.status]" :severity="statusSeverity[data.status]" />
        </template>
      </Column>
      <Column header="操作" style="min-width: 280px">
        <template #body="{ data }">
          <div class="flex gap-1 flex-wrap">
            <Button icon="pi pi-pencil" size="small" severity="info" @click="openEdit(data)" v-tooltip.top="'编辑'" />
            <Button
              v-if="isPrivileged && data.status === 'draft'"
              icon="pi pi-check"
              size="small"
              severity="warn"
              @click="doReview(data.id)"
              v-tooltip.top="'审核'"
            />
            <Button
              v-if="isPrivileged && data.status === 'reviewed'"
              icon="pi pi-check-circle"
              size="small"
              severity="success"
              @click="doApprove(data.id)"
              v-tooltip.top="'批准(联动闭环)'"
            />
            <Button
              v-if="isPrivileged && data.status === 'reviewed'"
              icon="pi pi-times-circle"
              size="small"
              severity="danger"
              @click="doReject(data.id)"
              v-tooltip.top="'驳回'"
            />
            <Button
              v-if="canBypass && data.status === 'reviewed'"
              icon="pi pi-forward"
              size="small"
              severity="warn"
              @click="openBypassException(data.id)"
              v-tooltip.top="'强制跳过'"
            />
            <Button icon="pi pi-trash" size="small" severity="danger" @click="remove(data.id)" v-tooltip.top="'删除'" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="showDialog"
      :header="(isEdit ? '编辑' : '新建') + '例外事项'"
      :style="{ width: '700px' }"
      :modal="true"
      class="p-fluid"
    >
      <div class="grid grid-cols-2 gap-4" style="max-height: 60vh; overflow-y: auto; padding-right: 4px">
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">例外信息</div>
        <div>
          <label class="block text-sm font-medium mb-1">例外类型 *</label>
          <Dropdown v-model="form.exception_type" :options="exceptionTypeOptions" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">关联项目ID</label>
          <InputText v-model="form.target_id" type="number" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">标题 *</label>
          <InputText v-model="form.title" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">事由说明</label>
          <Textarea v-model="form.reason" rows="3" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">处理结果</label>
          <Textarea v-model="form.resolution" rows="3" />
        </div>

        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">审批与管理</div>
        <div>
          <label class="block text-sm font-medium mb-1">状态</label>
          <Dropdown v-model="form.status" :options="statusOptions" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">负责部门</label>
          <Dropdown v-model="form.department_id" :options="departments" showClear placeholder="选择部门" />
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
        <p class="text-sm text-stone-600">您正在强制跳过例外事项审批，此操作将记录到审计日志。</p>
        <label class="form-label">跳过原因（必填）</label>
        <Textarea v-model="bypassReason" class="w-full" rows="3" placeholder="请填写强制跳过原因" />
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="bypassDialog = false" />
        <Button label="确认跳过" severity="warn" :disabled="!bypassReason.trim()" @click="doBypassException" />
      </template>
    </Dialog>
  </div>
</template>
