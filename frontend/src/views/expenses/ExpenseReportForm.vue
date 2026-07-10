<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useI18n } from '@/i18n'
import {
  listExpenseItems,
  createExpenseReport,
  getExpenseReport,
  updateExpenseReport,
  submitReport,
  listExpenseLoans,
  uploadAttachment,
  listAttachments,
  deleteAttachment,
  getReportItems,
} from '@/api/expenses'
import { listDepartments } from '@/api'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const userId = Number(localStorage.getItem('user_id') || '0')

const reportId = computed(() => (route.params.id ? Number(route.params.id) : null))
const isEdit = computed(() => !!reportId.value)

const expenseItems = ref<any[]>([])
const departments = ref<any[]>([])
const loans = ref<any[]>([])
const attachments = ref<any[]>([])
const saving = ref(false)
const uploading = ref(false)
const showAttachments = ref(false)

const form = ref({
  expense_date: new Date().toISOString().slice(0, 10),
  department_id: null as number | null,
  notes: '',
  items: [] as {
    row_seq: number
    expense_item_id: number | null
    date: string
    amount: number
    description: string
    receipt_count: number
  }[],
})

const policyWarnings = ref<any[]>([])

const uploadCategory = ref('发票')
const uploadDocNumber = ref('-')
const uploadFile = ref<File | null>(null)

const categoryOptions = [
  { label: '发票', value: '发票' },
  { label: '机票', value: '机票' },
  { label: '车票', value: '车票' },
  { label: '合同', value: '合同' },
  { label: '签收单', value: '签收单' },
  { label: '其他', value: '其他' },
]

const totalAmount = computed(() => form.value.items.reduce((s, i) => s + (i.amount || 0), 0))

const addItem = () => {
  form.value.items.push({
    row_seq: form.value.items.length + 1,
    expense_item_id: null,
    date: form.value.expense_date,
    amount: 0,
    description: '',
    receipt_count: 0,
  })
}

const removeItem = (idx: number) => {
  form.value.items.splice(idx, 1)
  form.value.items.forEach((it, i) => (it.row_seq = i + 1))
}

const fetchAll = async () => {
  try {
    const [itemsRes, deptRes, loansRes] = await Promise.all([
      listExpenseItems(companyId),
      listDepartments(companyId),
      listExpenseLoans(companyId),
    ])
    expenseItems.value = itemsRes.data
    departments.value = deptRes.data
    loans.value = loansRes.data.filter(
      (l: any) => l.applicant_id === userId && ['approved', 'partial_repaid'].includes(l.status),
    )
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

const loadReport = async () => {
  if (!reportId.value) return
  try {
    const [reportRes, itemsRes] = await Promise.all([getExpenseReport(reportId.value), getReportItems(reportId.value)])
    const r = reportRes.data
    form.value = {
      expense_date: r.expense_date,
      department_id: r.department_id,
      notes: r.notes || '',
      items: itemsRes.data.map((it: any) => ({
        row_seq: it.row_seq,
        expense_item_id: it.expense_item_id,
        date: it.date,
        amount: it.amount,
        description: it.description || '',
        receipt_count: it.receipt_count,
      })),
    }
    if (r.policy_warnings) policyWarnings.value = r.policy_warnings
    const attRes = await listAttachments(reportId.value)
    attachments.value = attRes.data
    showAttachments.value = true
  } catch (e: any) {
    toast.add({
      severity: 'error',
      summary: '加载报销单失败',
      detail: e.response?.data?.detail || e.message,
      life: 3000,
    })
  }
}

const saveDraft = async () => {
  saving.value = true
  try {
    const data = {
      company_id: companyId,
      expense_date: form.value.expense_date,
      department_id: form.value.department_id ?? undefined,
      notes: form.value.notes,
      items: form.value.items.map(it => ({
        row_seq: it.row_seq,
        expense_item_id: it.expense_item_id ?? undefined,
        date: it.date,
        amount: it.amount,
        description: it.description,
        receipt_count: it.receipt_count,
      })),
    }
    if (isEdit.value) {
      await updateExpenseReport(reportId.value!, data)
      toast.add({ severity: 'success', summary: '草稿已保存', life: 2000 })
    } else {
      const res = await createExpenseReport(data)
      toast.add({ severity: 'success', summary: '报销单已创建', life: 2000 })
      router.replace(`/finance/expenses/report-form/${res.data.id}`)
    }
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.saveFailed'), detail: e.response?.data?.detail || e.message, life: 3000 })
  } finally {
    saving.value = false
  }
}

const doSubmit = async () => {
  if (!reportId.value) {
    toast.add({ severity: 'warn', summary: '请先保存草稿', life: 3000 })
    return
  }
  saving.value = true
  try {
    const data = {
      company_id: companyId,
      expense_date: form.value.expense_date,
      department_id: form.value.department_id ?? undefined,
      notes: form.value.notes,
      items: form.value.items.map(it => ({
        row_seq: it.row_seq,
        expense_item_id: it.expense_item_id ?? undefined,
        date: it.date,
        amount: it.amount,
        description: it.description,
        receipt_count: it.receipt_count,
      })),
    }
    if (isEdit.value) await updateExpenseReport(reportId.value!, data)
    await submitReport(reportId.value)
    toast.add({ severity: 'success', summary: '报销单已提交审批', life: 2000 })
    router.push('/expenses/report-list')
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '提交失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  } finally {
    saving.value = false
  }
}

const onUpload = async () => {
  if (!uploadFile.value || !reportId.value) return
  uploading.value = true
  try {
    await uploadAttachment(reportId.value, uploadFile.value, uploadCategory.value, uploadDocNumber.value)
    toast.add({ severity: 'success', summary: '附件已上传', life: 2000 })
    uploadFile.value = null
    uploadDocNumber.value = '-'
    const attRes = await listAttachments(reportId.value)
    attachments.value = attRes.data
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '上传失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  } finally {
    uploading.value = false
  }
}

const onDeleteAttachment = async (attId: number) => {
  try {
    await deleteAttachment(attId)
    attachments.value = attachments.value.filter((a: any) => a.id !== attId)
    toast.add({ severity: 'success', summary: '附件已删除', life: 2000 })
  } catch (e: any) {
    toast.add({ severity: 'error', summary: t('common.deleteFailed'), detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

onMounted(async () => {
  await fetchAll()
  if (isEdit.value) await loadReport()
  else addItem()
})
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <h1 class="text-xl font-bold mb-4">{{ isEdit ? '编辑报销单' : '7.1 报销申请' }}</h1>

    <!-- Loan alert -->
    <div v-if="loans.length > 0" class="bg-yellow-50 border border-yellow-300 rounded-lg p-3 mb-4 text-sm">
      <i class="pi pi-info-circle text-yellow-600 mr-2" />
      您有 {{ loans.length }} 笔未还清借款，可在审批通过后冲销。
    </div>

    <!-- Basic info -->
    <div class="bg-white rounded-sm border border-stone-200 p-4 mb-4">
      <div class="grid grid-cols-3 gap-4">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">费用发生日期</label>
          <InputText type="date" v-model="form.expense_date" class="w-full" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">部门</label>
          <Dropdown
            v-model="form.department_id"
            :options="departments"
            optionLabel="name"
            optionValue="id"
            class="w-full"
            showClear
            placeholder="选择部门"
          />
        </div>
      </div>
    </div>

    <!-- Items table -->
    <div class="bg-white rounded-sm border border-stone-200 p-4 mb-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-semibold">费用明细</h2>
        <Button label="添加行" icon="pi pi-plus" size="small" severity="secondary" @click="addItem" />
      </div>
      <table class="w-full text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-2 text-left w-10">#</th>
            <th class="p-2 text-left">费用类型</th>
            <th class="p-2 text-left w-32">{{ t('common.date') }}</th>
            <th class="p-2 text-right w-32">{{ t('common.amount') }}</th>
            <th class="p-2 text-left">说明</th>
            <th class="p-2 text-right w-20">发票</th>
            <th class="p-2 text-center w-10"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, idx) in form.items"
            :key="idx"
            class="border-t"
            :class="{ 'bg-yellow-50': policyWarnings.some((w: any) => w.row_seq === item.row_seq) }"
          >
            <td class="p-2 text-gray-400 text-xs">{{ item.row_seq }}</td>
            <td class="p-2">
              <Dropdown
                v-model="item.expense_item_id"
                :options="expenseItems"
                optionLabel="name"
                optionValue="id"
                class="w-full"
                placeholder="选择"
              />
            </td>
            <td class="p-2">
              <InputText type="date" v-model="item.date" class="w-full" />
            </td>
            <td class="p-2 text-right">
              <InputNumber v-model="item.amount" class="w-full" :minFractionDigits="2" />
            </td>
            <td class="p-2">
              <InputText v-model="item.description" class="w-full" placeholder="费用说明" />
            </td>
            <td class="p-2 text-right">
              <InputNumber v-model="item.receipt_count" class="w-full" :min="0" showButtons />
            </td>
            <td class="p-2 text-center">
              <Button icon="pi pi-times" size="small" text rounded severity="danger" @click="removeItem(idx)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Policy warnings -->
    <div v-if="policyWarnings.length > 0" class="bg-yellow-50 border border-yellow-400 rounded-lg p-3 mb-4">
      <h3 class="text-sm font-bold text-yellow-700 mb-1">费用标准预警</h3>
      <ul class="text-sm text-yellow-600 list-disc list-inside">
        <li v-for="(w, i) in policyWarnings" :key="i">
          第{{ w.row_seq }}行: {{ w.description || '未说明' }} — 金额 {{ w.amount?.toLocaleString() }}，{{ w.message }}
        </li>
      </ul>
    </div>

    <!-- Attachments (edit mode) -->
    <div v-if="isEdit" class="bg-white rounded-sm border border-stone-200 p-4 mb-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-lg font-semibold">{{ t('expenses.attachments') }} ({{ attachments.length }})</h2>
        <Button
          label="展开上传"
          icon="pi pi-paperclip"
          size="small"
          severity="secondary"
          @click="showAttachments = !showAttachments"
        />
      </div>
      <div v-if="showAttachments">
        <div class="flex gap-2 items-end mb-3 flex-wrap">
          <div class="flex flex-col gap-1">
            <label class="text-xs">类别</label>
            <Dropdown
              v-model="uploadCategory"
              :options="categoryOptions"
              optionLabel="label"
              optionValue="value"
              class="w-28"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs">票据号码</label>
            <InputText v-model="uploadDocNumber" class="w-36" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs">文件</label>
            <input type="file" @change="(e: any) => (uploadFile = e.target.files?.[0] || null)" class="text-sm" />
          </div>
          <Button
            :label="t('common.upload')"
            icon="pi pi-upload"
            size="small"
            :loading="uploading"
            @click="onUpload"
            :disabled="!uploadFile"
          />
        </div>
        <div v-if="attachments.length > 0" class="flex flex-col gap-1">
          <div
            v-for="att in attachments"
            :key="att.id"
            class="flex items-center justify-between text-sm bg-gray-50 px-3 py-1 rounded"
          >
            <span class="font-mono text-xs">{{ att.file_name }}</span>
            <Button
              icon="pi pi-trash"
              size="small"
              text
              rounded
              severity="danger"
              @click="onDeleteAttachment(att.id)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Total + actions -->
    <div class="flex items-center justify-between border-t pt-4">
      <div class="text-lg font-bold">
        合计：{{ totalAmount.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}
      </div>
      <div class="flex gap-3">
        <Button label="保存草稿" icon="pi pi-save" severity="secondary" :loading="saving" @click="saveDraft" />
        <Button v-if="isEdit" label="提交审批" icon="pi pi-send" :loading="saving" @click="doSubmit" />
      </div>
    </div>
  </div>
</template>
