<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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
  listBidSubmissions,
  getBidOptions,
  createBidSubmission,
  updateBidSubmission,
  deleteBidSubmission,
} from '../../api/bids'
import api from '../../api'

const route = useRoute()
const confirm = useConfirm()

// ── 模式检测 ──
const modeLabels: Record<string, string> = {
  registrations: '投标登记',
  documents: '投标文件',
  pricing: '投标报价',
  bonds: '投标保证金',
}

const mode = computed(() => {
  const seg = route.path.split('/').pop() || 'registrations'
  return seg
})

const pageTitle = computed(() => modeLabels[mode.value] || '投标管理')

// ── 状态常量 ──
const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已递交', value: 'submitted' },
  { label: '已开标', value: 'opened' },
  { label: '已评标', value: 'evaluated' },
  { label: '中标', value: 'won' },
  { label: '未中标', value: 'lost' },
  { label: '已取消', value: 'cancelled' },
]

const statusLabels: Record<string, string> = Object.fromEntries(statusOptions.map(o => [o.value, o.label]))
const statusSeverity: Record<string, string> = {
  draft: 'info',
  submitted: 'warn',
  opened: 'warn',
  evaluated: 'warn',
  won: 'success',
  lost: 'danger',
  cancelled: 'secondary',
}

const bidTypeOptions = [
  { label: '公开投标', value: '公开投标' },
  { label: '邀请投标', value: '邀请投标' },
]

const bondStatusOptions = [
  { label: '未缴', value: '未缴' },
  { label: '已缴', value: '已缴' },
  { label: '已退', value: '已退' },
  { label: '被没收', value: '被没收' },
]

const bondSeverity: Record<string, string> = {
  未缴: 'info',
  已缴: 'warn',
  已退: 'success',
  被没收: 'danger',
}

// ── 数据状态 ──
const items = ref<any[]>([])
const loading = ref(false)
const departments = ref<any[]>([])

// 筛选
const fBidType = ref<string[]>([])
const fBondStatus = ref<string[]>([])
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
    bid_no: `TB-${now.replace(/-/g, '')}-`,
    project_name: '',
    tendering_party: '',
    tendering_agency: '',
    bid_type: '公开投标',
    department_id: null,
    owner_id: null,
    bid_amount: 0,
    currency: 'CNY',
    bond_amount: 0,
    bond_paid_date: null,
    bond_returned_date: null,
    bond_status: '未缴',
    bid_doc_submitted_date: null,
    bid_deadline: null,
    opening_date: null,
    technical_score: null,
    price_score: null,
    total_score: null,
    rank: null,
    status: 'draft',
    result_notes: '',
    bid_doc_path: '',
    notes: '',
  }
}

// ── 数据加载 ──
async function load() {
  loading.value = true
  try {
    const r = await listBidSubmissions({
      company_id: Number(localStorage.getItem('company_id') || '1'),
      bid_type: fBidType.value.length > 0 ? fBidType.value.join(',') : undefined,
      bond_status: fBondStatus.value.length > 0 ? fBondStatus.value.join(',') : undefined,
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
      await updateBidSubmission(form.value.id, form.value)
    } else {
      await createBidSubmission(form.value)
    }
    showDialog.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

function remove(id: number) {
  confirm.require({
    message: '确认删除该投标项目？',
    header: '确认删除',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      await deleteBidSubmission(id)
      await load()
    },
  })
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
      <Button v-if="mode === 'registrations'" label="新建投标登记" icon="pi pi-plus" @click="openCreate" />
    </div>

    <!-- 筛选栏 -->
    <Toolbar class="mb-4">
      <template #start>
        <div class="flex flex-wrap gap-3">
          <MultiSelect v-model="fBidType" :options="bidTypeOptions" placeholder="投标类型" class="w-36" />
          <MultiSelect
            v-if="mode === 'bonds'"
            v-model="fBondStatus"
            :options="bondStatusOptions"
            placeholder="保证金状态"
            class="w-36"
          />
          <Dropdown v-model="fStatus" :options="statusOptions" placeholder="状态" class="w-32" showClear />
          <InputText v-model="fSearch" placeholder="搜索编号/名称/招标方" class="w-52" @keyup.enter="load" />
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
      <Column field="bid_no" header="投标编号" style="min-width: 140px" />
      <Column field="project_name" header="项目名称" style="min-width: 200px" />
      <Column field="tendering_party" header="招标方" style="min-width: 140px" />
      <Column field="bid_amount" header="投标报价" style="min-width: 100px">
        <template #body="{ data }">{{ data.bid_amount?.toLocaleString() }}</template>
      </Column>
      <Column field="bond_status" header="保证金" style="min-width: 80px">
        <template #body="{ data }">
          <Tag :value="data.bond_status" :severity="bondSeverity[data.bond_status] || 'info'" />
        </template>
      </Column>
      <Column field="opening_date" header="开标日期" style="min-width: 100px" />
      <Column v-if="mode === 'pricing'" field="total_score" header="总得分" style="min-width: 80px" />
      <Column v-if="mode === 'pricing'" field="rank" header="排名" style="min-width: 60px" />
      <Column field="status" header="状态" style="min-width: 90px">
        <template #body="{ data }">
          <Tag :value="statusLabels[data.status]" :severity="statusSeverity[data.status]" />
        </template>
      </Column>
      <Column header="操作" style="min-width: 120px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button
              v-if="mode === 'registrations'"
              icon="pi pi-pencil"
              size="small"
              severity="info"
              @click="openEdit(data)"
              v-tooltip.top="'编辑'"
            />
            <Button
              v-if="mode === 'registrations'"
              icon="pi pi-trash"
              size="small"
              severity="danger"
              @click="remove(data)"
              v-tooltip.top="'删除'"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- 编辑/创建对话框 -->
    <Dialog
      v-model:visible="showDialog"
      :header="(isEdit ? '编辑' : '新建') + '投标项目'"
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
          <label class="block text-sm font-medium mb-1">投标编号</label>
          <InputText v-model="form.bid_no" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">招标方</label>
          <InputText v-model="form.tendering_party" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">招标代理机构</label>
          <InputText v-model="form.tendering_agency" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">投标类型</label>
          <Dropdown v-model="form.bid_type" :options="bidTypeOptions" />
        </div>

        <!-- 报价 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">投标报价</div>
        <div>
          <label class="block text-sm font-medium mb-1">投标金额</label>
          <InputNumber v-model="form.bid_amount" mode="currency" currency="CNY" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">币种</label>
          <InputText v-model="form.currency" />
        </div>

        <!-- 保证金 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">投标保证金</div>
        <div>
          <label class="block text-sm font-medium mb-1">保证金金额</label>
          <InputNumber v-model="form.bond_amount" mode="currency" currency="CNY" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">保证金状态</label>
          <Dropdown v-model="form.bond_status" :options="bondStatusOptions" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">缴纳日期</label>
          <DatePicker v-model="form.bond_paid_date" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">退还日期</label>
          <DatePicker v-model="form.bond_returned_date" class="w-full" />
        </div>

        <!-- 时间节点 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">时间节点</div>
        <div>
          <label class="block text-sm font-medium mb-1">投标文件递交日期</label>
          <DatePicker v-model="form.bid_doc_submitted_date" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">投标截止日期</label>
          <DatePicker v-model="form.bid_deadline" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">开标日期</label>
          <DatePicker v-model="form.opening_date" class="w-full" />
        </div>

        <!-- 评分 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">评标得分</div>
        <div>
          <label class="block text-sm font-medium mb-1">技术得分</label>
          <InputNumber v-model="form.technical_score" mode="decimal" :minFractionDigits="1" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">价格得分</label>
          <InputNumber v-model="form.price_score" mode="decimal" :minFractionDigits="1" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">总得分</label>
          <InputNumber v-model="form.total_score" mode="decimal" :minFractionDigits="1" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">排名</label>
          <InputNumber v-model="form.rank" mode="decimal" :minFractionDigits="0" class="w-full" />
        </div>

        <!-- 结果 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">投标结果</div>
        <div>
          <label class="block text-sm font-medium mb-1">状态</label>
          <Dropdown v-model="form.status" :options="statusOptions" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium mb-1">结果备注</label>
          <Textarea v-model="form.result_notes" rows="2" />
        </div>

        <!-- 文件 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">投标文件</div>
        <div>
          <label class="block text-sm font-medium mb-1">投标文件路径</label>
          <InputText v-model="form.bid_doc_path" />
        </div>

        <!-- 管理 -->
        <div class="col-span-2 font-bold text-lg border-b pb-1 mb-1">管理</div>
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
  </div>
</template>
