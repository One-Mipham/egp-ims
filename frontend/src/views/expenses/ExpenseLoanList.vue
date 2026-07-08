<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useI18n } from '@/i18n'
import { listExpenseLoans, createExpenseLoan, approveLoan, repayLoan, bypassLoan } from '@/api/expenses'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'

const { t } = useI18n()
const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const loans = ref<any[]>([])
const loading = ref(false)
const dialog = ref(false)
const repayDialog = ref(false)
const currentLoan = ref<any>(null)
const repayAmount = ref(0)

const currentUserRole = ref(localStorage.getItem('role') || '')
const canBypass = computed(() => ['super_admin', 'finance_director'].includes(currentUserRole.value))

const bypassDialog = ref(false)
const bypassReason = ref('')
const currentLoanId = ref<number | null>(null)

const openBypass = (id: number) => { currentLoanId.value = id; bypassReason.value = ''; bypassDialog.value = true }

const doBypass = async () => {
  try {
    await bypassLoan(currentLoanId.value!, bypassReason.value)
    toast.add({ severity: 'success', summary: '已强制跳过', life: 2000 })
    bypassDialog.value = false; fetchLoans()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

const form = ref({
  loan_date: new Date().toISOString().slice(0, 10),
  amount: 0, reason: '', expected_repay_date: '', notes: '',
})

const statusLabels: Record<string, string> = {
  submitted: '待审批', approved: '已批准',
  partial_repaid: '部分已还', fully_repaid: '已还清', closed: '已归档',
}

const fetchLoans = async () => {
  loading.value = true
  try {
    const res = await listExpenseLoans(companyId)
    loans.value = res.data
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e.message, life: 3000 })
  } finally { loading.value = false }
}

const createNew = async () => {
  try {
    await createExpenseLoan({
      company_id: companyId, loan_date: form.value.loan_date,
      amount: form.value.amount, reason: form.value.reason,
      expected_repay_date: form.value.expected_repay_date || undefined,
      notes: form.value.notes || undefined,
    })
    toast.add({ severity: 'success', summary: '借款申请已提交', life: 2000 })
    dialog.value = false; fetchLoans()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '提交失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

const doApprove = async (id: number) => {
  try {
    await approveLoan(id)
    toast.add({ severity: 'success', summary: '借款已批准', life: 2000 })
    fetchLoans()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.message, life: 3000 })
  }
}

const openRepay = (loan: any) => {
  currentLoan.value = loan
  repayAmount.value = loan.amount - loan.repaid_amount
  repayDialog.value = true
}

const doRepay = async () => {
  try {
    await repayLoan(currentLoan.value.id, repayAmount.value)
    toast.add({ severity: 'success', summary: '还款记录已保存', life: 2000 })
    repayDialog.value = false; fetchLoans()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.message, life: 3000 })
  }
}

onMounted(fetchLoans)
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold">7.3 借款管理</h1>
      <Button label="新增借款申请" icon="pi pi-plus" @click="dialog = true; form = { loan_date: new Date().toISOString().slice(0,10), amount: 0, reason: '', expected_repay_date: '', notes: '' }" />
    </div>

    <DataTable :value="loans" :loading="loading" stripedRows size="small" class="text-sm">
      <Column field="loan_no" header="借款单号" class="font-mono" />
      <Column header="借款人">
        <template #body="slotProps">{{ slotProps.data.applicant_id }}</template>
      </Column>
      <Column field="loan_date" header="借款日期" />
      <Column header="借款金额">
        <template #body="slotProps">¥{{ slotProps.data.amount?.toLocaleString() }}</template>
      </Column>
      <Column header="已还金额">
        <template #body="slotProps">¥{{ slotProps.data.repaid_amount?.toLocaleString() }}</template>
      </Column>
      <Column :header="t('common.status')">
        <template #body="slotProps">
          <Tag :value="statusLabels[slotProps.data.status] || slotProps.data.status" />
        </template>
      </Column>
      <Column :header="t('common.actions')" style="width:8rem">
        <template #body="slotProps">
          <Button v-if="slotProps.data.status === 'submitted'" icon="pi pi-check" size="small" text rounded severity="success" @click="doApprove(slotProps.data.id)" />
          <Button v-if="canBypass && slotProps.data.status === 'submitted'" icon="pi pi-forward" size="small" text rounded severity="warn" @click="openBypass(slotProps.data.id)" v-tooltip.top="'强制跳过'" />
          <Button v-if="['approved', 'partial_repaid'].includes(slotProps.data.status)" :label="t('expenses.repayLoan')" size="small" text @click="openRepay(slotProps.data)" />
        </template>
      </Column>
    </DataTable>

    <!-- Create dialog -->
    <Dialog v-model:visible="dialog" header="新增借款申请" :modal="true" :style="{ width: '28rem' }">
      <div class="flex flex-col gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">借款日期</label>
          <InputText type="date" v-model="form.loan_date" class="w-full" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">借款金额 <span class="text-red-500">*</span></label>
          <InputNumber v-model="form.amount" class="w-full" :minFractionDigits="2" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">借款事由</label>
          <Textarea v-model="form.reason" class="w-full" rows="2" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">预计还款日期</label>
          <InputText type="date" v-model="form.expected_repay_date" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="dialog = false" />
        <Button :label="t('common.submit')" @click="createNew" />
      </template>
    </Dialog>

    <!-- Repay dialog -->
    <Dialog v-model:visible="repayDialog" header="还款" :modal="true" :style="{ width: '20rem' }">
      <div class="flex flex-col gap-3">
        <p class="text-sm">未还金额: ¥{{ ((currentLoan?.amount || 0) - (currentLoan?.repaid_amount || 0)).toLocaleString() }}</p>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">还款金额</label>
          <InputNumber v-model="repayAmount" class="w-full" :minFractionDigits="2" :max="(currentLoan?.amount || 0) - (currentLoan?.repaid_amount || 0)" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="repayDialog = false" />
        <Button label="确认还款" @click="doRepay" />
      </template>
    </Dialog>

    <!-- Bypass dialog -->
    <Dialog v-model:visible="bypassDialog" header="强制跳过审批" :modal="true" :style="{ width: '28rem' }">
      <div class="flex flex-col gap-3">
        <p class="text-sm text-stone-600">您正在强制跳过借款审批，此操作将记录到审计日志。</p>
        <label class="form-label">跳过原因（必填）</label>
        <Textarea v-model="bypassReason" class="w-full" rows="3" placeholder="请填写强制跳过原因" />
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="bypassDialog = false" />
        <Button label="确认跳过" severity="warn" :disabled="!bypassReason.trim()" @click="doBypass" />
      </template>
    </Dialog>
  </div>
</template>
