<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useI18n } from '@/i18n'
import {
  listContracts,
  getContractCategories,
  getLegalBasisOptions,
  createContract,
  updateContract,
  deleteContract,
  reviewContract,
  approveContract,
  sealContract,
  uploadContractScan,
  confirmContractClosure,
} from '@/api/contracts'
import { listDepartments } from '@/api'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import FileUpload from 'primevue/fileupload'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { t } = useI18n()
const companyId = Number(localStorage.getItem('companyId') || '1')
const userId = Number(localStorage.getItem('user_id') || '0')

const contractType = ref<string>('')
const typeLabels: Record<string, string> = {
  supplier: '供应商合同',
  customer: '客户合同',
  labor: '劳动合同',
  lease: '租赁合同',
}

watch(
  () => route.path,
  () => {
    detectType()
  },
  { immediate: true },
)
function detectType() {
  const p = route.path
  if (p.includes('/contracts/supplier')) contractType.value = 'supplier'
  else if (p.includes('/contracts/customer')) contractType.value = 'customer'
  else if (p.includes('/contracts/labor')) contractType.value = 'labor'
  else if (p.includes('/contracts/lease')) contractType.value = 'lease'
}

const items = ref<any[]>([])
const loading = ref(false)

const fDepartmentIds = ref<number[]>([])
const fCategories = ref<string[]>([])
const fStatus = ref<string>('')
const fSearch = ref('')

const departments = ref<any[]>([])
const categories = ref<string[]>([])
const legalBasisOptions = ref<string[]>([])

const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const form = ref<any>({})

// Scan dialog
const showScanDialog = ref(false)
const scanContractId = ref<number | null>(null)
const scanFile = ref<File | null>(null)

// Closure dialog
const showClosureDialog = ref(false)
const closureContractId = ref<number | null>(null)

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '履行中', value: 'active' },
  { label: '已完成', value: 'completed' },
  { label: '已终止', value: 'terminated' },
]
const contractTypeOptions = [
  { label: '供应商合同', value: 'supplier' },
  { label: '客户合同', value: 'customer' },
  { label: '劳动合同', value: 'labor' },
  { label: '租赁合同', value: 'lease' },
]
const statusLabels: Record<string, string> = {
  draft: '草稿',
  active: '履行中',
  completed: '已完成',
  terminated: '已终止',
}
const statusSeverity: Record<string, string> = {
  draft: 'secondary',
  active: 'success',
  completed: 'info',
  terminated: 'danger',
}

async function loadRefs() {
  try {
    const [deptRes, catRes, legalRes] = await Promise.all([
      listDepartments(companyId),
      getContractCategories(),
      getLegalBasisOptions(),
    ])
    departments.value = deptRes.data.map((d: any) => ({ label: d.name, value: d.id }))
    categories.value = catRes.data
    legalBasisOptions.value = legalRes.data
  } catch (_e) {}
}

async function load() {
  loading.value = true
  try {
    const params: any = { company_id: companyId }
    if (contractType.value) params.contract_type = contractType.value
    if (fDepartmentIds.value.length) params.department_id = fDepartmentIds.value.join(',')
    if (fCategories.value.length) params.contract_category = fCategories.value.join(',')
    if (fStatus.value) params.status = fStatus.value
    if (fSearch.value) params.search = fSearch.value
    const { data } = await listContracts(params)
    items.value = data
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.message, life: 3000 })
  } finally {
    loading.value = false
  }
}

function emptyForm() {
  return {
    company_id: companyId,
    contract_no: '',
    contract_type: contractType.value || 'supplier',
    contract_category: '其他',
    contract_name: '',
    subject: '',
    legal_basis: '',
    legal_basis_arr: [],
    party_a: '',
    party_a_address: '',
    party_a_phone: '',
    party_a_representative: '',
    party_a_signatory: '',
    party_b: '',
    party_b_address: '',
    party_b_phone: '',
    party_b_representative: '',
    party_b_signatory: '',
    amount: 0,
    sign_date: '',
    start_date: '',
    end_date: '',
    payment_terms: '',
    force_majeure: '',
    arbitration_venue: '',
    execution_progress: '',
    supplement_notes: '',
    status: 'draft',
    department_id: null,
    owner_id: userId,
    notes: '',
  }
}
function openCreate() {
  form.value = emptyForm()
  isEdit.value = false
  showDialog.value = true
}
function openEdit(row: any) {
  form.value = {
    ...row,
    company_id: row.company_id || companyId,
    legal_basis_arr: row.legal_basis ? row.legal_basis.split(',') : [],
  }
  isEdit.value = true
  editId.value = row.id
  showDialog.value = true
}
async function save() {
  try {
    const payload = { ...form.value }
    delete payload.id
    delete payload.created_at
    delete payload.updated_at
    delete payload.legal_basis_arr
    delete payload.scan_file_path
    delete payload.archived_at
    delete payload.reviewed_at
    delete payload.approved_at
    delete payload.sealed_at
    delete payload.closure_confirmed_at
    if (isEdit.value && editId.value) {
      await updateContract(editId.value, payload)
      toast.add({ severity: 'success', summary: t('common.updateSuccess'), life: 2000 })
    } else {
      await createContract(payload)
      toast.add({ severity: 'success', summary: t('common.addSuccess'), life: 2000 })
    }
    showDialog.value = false
    load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}
async function remove(id: number) {
  try {
    await deleteContract(id)
    toast.add({ severity: 'success', summary: t('common.deleteSuccess'), life: 2000 })
    load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.message, life: 3000 })
  }
}

// Workflow
async function doReview(id: number) {
  try {
    await reviewContract(id)
    toast.add({ severity: 'success', summary: '已审核', life: 2000 })
    load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.message, life: 3000 })
  }
}
async function doApprove(id: number) {
  try {
    await approveContract(id)
    toast.add({ severity: 'success', summary: '已批准', life: 2000 })
    load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.message, life: 3000 })
  }
}
async function doSeal(id: number) {
  try {
    await sealContract(id)
    toast.add({ severity: 'success', summary: '已盖章', life: 2000 })
    load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.message, life: 3000 })
  }
}

// Scan
function openScan(id: number) {
  scanContractId.value = id
  scanFile.value = null
  showScanDialog.value = true
}
async function doUpload() {
  if (!scanFile.value || !scanContractId.value) return
  try {
    await uploadContractScan(scanContractId.value, scanFile.value)
    toast.add({ severity: 'success', summary: '扫描件已上传', life: 2000 })
    showScanDialog.value = false
    load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.message, life: 3000 })
  }
}
function onFileSelect(e: any) {
  scanFile.value = e.files[0]
}

// Closure
function openClosure(id: number) {
  closureContractId.value = id
  showClosureDialog.value = true
}
async function doClosure() {
  if (!closureContractId.value) return
  try {
    await confirmContractClosure(closureContractId.value)
    toast.add({ severity: 'success', summary: '闭环确认完成', life: 2000 })
    showClosureDialog.value = false
    load()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.message, life: 3000 })
  }
}

function goPrint(id: number) {
  router.push(`/finance/contracts/print/${id}`)
}
function fmtDate(v: string) {
  if (!v) return ''
  return v.length === 10 ? v : v.slice(0, 10)
}

onMounted(async () => {
  detectType()
  await loadRefs()
  load()
})
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold">{{ typeLabels[contractType] || t('contracts.title') }}</h1>
      <Button :label="t('contracts.addContract')" icon="pi pi-plus" @click="openCreate" />
    </div>

    <div class="flex flex-wrap gap-3 mb-4 items-center">
      <MultiSelect
        v-model="fDepartmentIds"
        :options="departments"
        placeholder="发起部门"
        class="w-48"
        display="chip"
        @change="load"
      />
      <MultiSelect
        v-model="fCategories"
        :options="categories"
        :placeholder="t('contracts.categories')"
        class="w-56"
        display="chip"
        @change="load"
      />
      <Dropdown v-model="fStatus" :options="statusOptions" :placeholder="t('common.status')" class="w-36" showClear @change="load" />
      <InputText v-model="fSearch" :placeholder="t('common.searchPlaceholder')" class="w-48" @keyup.enter="load" />
      <Button icon="pi pi-search" severity="secondary" @click="load" />
    </div>

    <DataTable
      :value="items"
      :loading="loading"
      paginator
      :rows="15"
      :rowsPerPageOptions="[15, 30, 50]"
      stripedRows
      sortField="id"
      :sortOrder="-1"
    >
      <Column field="contract_no" :header="t('contracts.contractNo')" style="min-width: 140px" sortable />
      <Column field="contract_name" :header="t('contracts.contractName')" style="min-width: 160px" sortable />
      <Column field="contract_category" :header="t('contracts.categories')" style="min-width: 110px" sortable />
      <Column :header="t('contracts.partyB')" style="min-width: 120px" sortable sortField="party_b">
        <template #body="{ data }">{{ data.party_b || '-' }}</template>
      </Column>
      <Column field="amount" :header="t('contracts.contractAmount')" style="min-width: 100px" sortable>
        <template #body="{ data }">¥{{ data.amount?.toLocaleString() }}</template>
      </Column>
      <Column field="sign_date" :header="t('contracts.signDate')" style="min-width: 90px" sortable>
        <template #body="{ data }">{{ fmtDate(data.sign_date) }}</template>
      </Column>
      <Column header="流程" style="min-width: 130px">
        <template #body="{ data }">
          <div class="flex gap-0.5 flex-wrap">
            <Tag v-if="data.reviewed_at" value="已审" severity="info" class="text-xs" />
            <Tag v-if="data.approved_at" value="已批" severity="success" class="text-xs" />
            <Tag v-if="data.sealed_at" value="已盖章" severity="warn" class="text-xs" />
            <Tag v-if="data.scan_file_path" value="已扫描" severity="info" class="text-xs" />
            <Tag v-if="data.closure_confirmed" value="已闭环" severity="success" class="text-xs" />
            <span v-if="!data.reviewed_at && !data.approved_at && !data.sealed_at" class="text-gray-400 text-xs"
              >未启动</span
            >
          </div>
        </template>
      </Column>
      <Column field="status" :header="t('contracts.contractStatus')" style="min-width: 80px">
        <template #body="{ data }">
          <Tag :value="statusLabels[data.status] || data.status" :severity="statusSeverity[data.status]" />
        </template>
      </Column>
      <Column :header="t('common.actions')" style="min-width: 280px">
        <template #body="{ data }">
          <div class="flex gap-1 flex-wrap">
            <Button icon="pi pi-pencil" severity="info" size="small" @click="openEdit(data)" v-tooltip.top="t('common.edit')" />
            <Button
              v-if="!data.reviewed_at"
              icon="pi pi-check-circle"
              severity="help"
              size="small"
              @click="doReview(data.id)"
              v-tooltip.top="t('contracts.reviewContract')"
            />
            <Button
              v-if="data.reviewed_at && !data.approved_at"
              icon="pi pi-check"
              severity="success"
              size="small"
              @click="doApprove(data.id)"
              v-tooltip.top="t('contracts.approveContract')"
            />
            <Button
              v-if="data.approved_at && !data.sealed_at"
              icon="pi pi-lock"
              severity="warn"
              size="small"
              @click="doSeal(data.id)"
              v-tooltip.top="t('contracts.sealContract')"
            />
            <Button
              v-if="!data.scan_file_path"
              icon="pi pi-upload"
              severity="secondary"
              size="small"
              @click="openScan(data.id)"
              v-tooltip.top="t('contracts.scanContract')"
            />
            <Button
              icon="pi pi-print"
              severity="secondary"
              size="small"
              @click="goPrint(data.id)"
              v-tooltip.top="t('contracts.print')"
            />
            <Button
              v-if="!data.closure_confirmed"
              icon="pi pi-lock-open"
              severity="contrast"
              size="small"
              @click="openClosure(data.id)"
              v-tooltip.top="t('contracts.closureConfirm')"
            />
            <Button icon="pi pi-trash" severity="danger" size="small" @click="remove(data.id)" v-tooltip.top="t('common.delete')" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Edit Dialog -->
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? t('contracts.editContract') : t('contracts.addContract')"
      :style="{ width: '900px' }"
      :modal="true"
    >
      <div class="grid grid-cols-2 gap-4 max-h-[70vh] overflow-y-auto px-1">
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.contractName') }}</label
          ><InputText v-model="form.contract_name" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.contractNo') }}</label
          ><InputText v-model="form.contract_no" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.contractType') }}</label
          ><Dropdown v-model="form.contract_type" :options="contractTypeOptions" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.categories') }}</label
          ><Dropdown v-model="form.contract_category" :options="categories" class="w-full" editable />
        </div>
        <div class="field col-span-2">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.legalBasis') }}（可多选）</label>
          <MultiSelect
            v-model="form.legal_basis_arr"
            :options="legalBasisOptions"
            class="w-full"
            placeholder="勾选适用法律..."
            display="chip"
            @change="form.legal_basis = form.legal_basis_arr?.join(',')"
          />
        </div>
        <div class="field col-span-2">
          <label class="block text-xs font-semibold mb-1">合同事由</label
          ><InputText v-model="form.subject" class="w-full" />
        </div>

        <div class="col-span-2 mt-2"><h3 class="text-sm font-bold border-b pb-1">{{ t('contracts.partyA') }}信息（我方）</h3></div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('common.name') }}</label
          ><InputText v-model="form.party_a" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">法定代表人</label
          ><InputText v-model="form.party_a_representative" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">地址</label
          ><InputText v-model="form.party_a_address" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">电话</label
          ><InputText v-model="form.party_a_phone" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">授权签字人</label
          ><InputText v-model="form.party_a_signatory" class="w-full" />
        </div>

        <div class="col-span-2 mt-2"><h3 class="text-sm font-bold border-b pb-1">{{ t('contracts.partyB') }}信息（对方）</h3></div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('common.name') }}</label
          ><InputText v-model="form.party_b" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">法定代表人</label
          ><InputText v-model="form.party_b_representative" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">地址</label
          ><InputText v-model="form.party_b_address" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">电话</label
          ><InputText v-model="form.party_b_phone" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">授权签字人</label
          ><InputText v-model="form.party_b_signatory" class="w-full" />
        </div>

        <div class="col-span-2 mt-2"><h3 class="text-sm font-bold border-b pb-1">金额与日期</h3></div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.contractAmount') }}</label
          ><InputNumber v-model="form.amount" class="w-full" mode="currency" currency="CNY" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.signDate') }}</label
          ><DatePicker v-model="form.sign_date" class="w-full" dateFormat="yy-mm-dd" showIcon />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.startDate') }}</label
          ><DatePicker v-model="form.start_date" class="w-full" dateFormat="yy-mm-dd" showIcon />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.endDate') }}</label
          ><DatePicker v-model="form.end_date" class="w-full" dateFormat="yy-mm-dd" showIcon />
        </div>

        <div class="col-span-2 mt-2"><h3 class="text-sm font-bold border-b pb-1">关键条款</h3></div>
        <div class="field col-span-2">
          <label class="block text-xs font-semibold mb-1">财务支付条款</label
          ><Textarea v-model="form.payment_terms" class="w-full" rows="3" placeholder="付款方式、金额、时间节点..." />
        </div>
        <div class="field col-span-2">
          <label class="block text-xs font-semibold mb-1">不可抗力条款</label
          ><Textarea v-model="form.force_majeure" class="w-full" rows="2" placeholder="不可抗力事件定义及处理..." />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">仲裁/诉讼地</label
          ><InputText v-model="form.arbitration_venue" class="w-full" />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('contracts.contractStatus') }}</label
          ><Dropdown v-model="form.status" :options="statusOptions" class="w-full" />
        </div>

        <div class="col-span-2 mt-2"><h3 class="text-sm font-bold border-b pb-1">执行与补录</h3></div>
        <div class="field col-span-2">
          <label class="block text-xs font-semibold mb-1">执行进展</label
          ><Textarea v-model="form.execution_progress" class="w-full" rows="2" placeholder="合同履行进展情况记录..." />
        </div>
        <div class="field col-span-2">
          <label class="block text-xs font-semibold mb-1">补录说明</label
          ><Textarea v-model="form.supplement_notes" class="w-full" rows="2" placeholder="补充录入说明..." />
        </div>

        <div class="col-span-2 mt-2"><h3 class="text-sm font-bold border-b pb-1">管理信息</h3></div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">发起部门</label
          ><Dropdown
            v-model="form.department_id"
            :options="departments"
            class="w-full"
            showClear
            :placeholder="t('common.pleaseSelect')"
          />
        </div>
        <div class="field">
          <label class="block text-xs font-semibold mb-1">{{ t('common.remark') }}</label
          ><Textarea v-model="form.notes" class="w-full" rows="2" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="showDialog = false" />
        <Button :label="t('common.save')" icon="pi pi-check" @click="save" />
      </template>
    </Dialog>

    <!-- Scan Upload Dialog -->
    <Dialog v-model:visible="showScanDialog" :header="t('contracts.scanContract')" :style="{ width: '400px' }" :modal="true">
      <FileUpload
        mode="basic"
        name="file"
        :maxFileSize="10000000"
        accept="image/*,application/pdf"
        @select="onFileSelect"
        :chooseLabel="t('contracts.scanContract')"
      />
      <div class="mt-2 text-sm text-gray-500">支持 PDF、JPG、PNG，最大 10MB</div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="showScanDialog = false" />
        <Button :label="t('common.upload')" icon="pi pi-upload" @click="doUpload" :disabled="!scanFile" />
      </template>
    </Dialog>

    <!-- Closure Confirm Dialog -->
    <Dialog v-model:visible="showClosureDialog" :header="t('contracts.closureConfirm')" :style="{ width: '400px' }" :modal="true">
      <p class="text-sm">确认该合同已执行完毕，所有条款已履行？</p>
      <p class="text-xs text-gray-500 mt-2">确认后合同状态将变更为"已完成"。</p>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="showClosureDialog = false" />
        <Button :label="t('contracts.closureConfirm')" icon="pi pi-check" severity="success" @click="doClosure" />
      </template>
    </Dialog>
  </div>
</template>
