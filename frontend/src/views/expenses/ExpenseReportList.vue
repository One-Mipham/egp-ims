<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { listExpenseReports, approveReport, rejectReport, cancelReport, bypassReport } from '@/api/expenses'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Textarea from 'primevue/textarea'

const router = useRouter()
const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const userId = Number(localStorage.getItem('user_id') || '0')
const reports = ref<any[]>([])
const loading = ref(false)
const activeTab = ref(0)
const approveDialog = ref(false)
const rejectDialog = ref(false)
const currentReport = ref<any>(null)
const comment = ref('')

const currentUserRole = ref(localStorage.getItem('role') || '')
const canBypass = computed(() => ['super_admin', 'finance_director'].includes(currentUserRole.value))

const bypassDialog = ref(false)
const bypassReason = ref('')

const openBypass = (r: any) => { currentReport.value = r; bypassReason.value = ''; bypassDialog.value = true }

const doBypass = async () => {
  try {
    await bypassReport(currentReport.value.id, bypassReason.value)
    toast.add({ severity: 'success', summary: '已强制跳过', life: 2000 })
    bypassDialog.value = false; fetchReports()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

const statusLabels: Record<string, string> = {
  draft: '草稿', submitted: '待审批', dept_approved: '部门已批',
  finance_approved: '财务已批', director_approved: '总监已批',
  unit_head_approved: '已审批', paid: '已付款', closed: '已归档', rejected: '已驳回',
}

const statusSeverity: Record<string, string> = {
  draft: 'secondary', submitted: 'info', dept_approved: 'warn',
  finance_approved: 'warn', director_approved: 'warn',
  unit_head_approved: 'success', paid: 'success', closed: 'success', rejected: 'danger',
}

const fetchReports = async () => {
  loading.value = true
  try {
    const res = await listExpenseReports(companyId)
    reports.value = res.data
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  } finally { loading.value = false }
}

const filteredReports = computed(() => {
  if (activeTab.value === 0) return reports.value.filter((r: any) => r.applicant_id === userId)
  if (activeTab.value === 1) return reports.value.filter((r: any) => r.current_approver_id === userId)
  return reports.value
})

const openApprove = (r: any) => { currentReport.value = r; comment.value = ''; approveDialog.value = true }
const openReject = (r: any) => { currentReport.value = r; comment.value = ''; rejectDialog.value = true }

const doApprove = async () => {
  try {
    await approveReport(currentReport.value.id, comment.value || undefined)
    toast.add({ severity: 'success', summary: '已批准', life: 2000 })
    approveDialog.value = false; fetchReports()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

const doReject = async () => {
  try {
    await rejectReport(currentReport.value.id, comment.value || undefined)
    toast.add({ severity: 'success', summary: '已驳回', life: 2000 })
    rejectDialog.value = false; fetchReports()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

const doCancel = async (id: number) => {
  try {
    await cancelReport(id)
    toast.add({ severity: 'success', summary: '已撤回', life: 2000 })
    fetchReports()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '撤回失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

onMounted(fetchReports)
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold">7.2 报销列表</h1>
      <Button label="新建报销单" icon="pi pi-plus" @click="router.push('/expenses/report-form')" />
    </div>

    <TabView v-model:activeIndex="activeTab">
      <TabPanel value="0" header="我的报销" />
      <TabPanel value="1" header="待我审批" />
      <TabPanel value="2" header="全部报销" />
    </TabView>

    <DataTable :value="filteredReports" :loading="loading" stripedRows size="small" class="text-sm">
      <Column field="report_no" header="单号" class="font-mono" />
      <Column header="申请人">
        <template #body="slotProps">{{ slotProps.data.applicant_id }}</template>
      </Column>
      <Column field="expense_date" header="费用日期" />
      <Column header="金额">
        <template #body="slotProps">{{ slotProps.data.total_amount?.toLocaleString() }}</template>
      </Column>
      <Column header="状态">
        <template #body="slotProps">
          <Tag :value="statusLabels[slotProps.data.status] || slotProps.data.status" :severity="statusSeverity[slotProps.data.status] || 'secondary'" />
        </template>
      </Column>
      <Column header="操作" style="width:12rem">
        <template #body="slotProps">
          <div class="flex gap-1">
            <Button icon="pi pi-eye" size="small" text rounded @click="router.push(`/finance/expenses/report-form/${slotProps.data.id}`)" />
            <Button v-if="slotProps.data.current_approver_id === userId" icon="pi pi-check" size="small" text rounded severity="success" @click="openApprove(slotProps.data)" />
            <Button v-if="slotProps.data.current_approver_id === userId" icon="pi pi-times" size="small" text rounded severity="danger" @click="openReject(slotProps.data)" />
            <Button v-if="slotProps.data.applicant_id === userId && ['submitted', 'dept_approved'].includes(slotProps.data.status)" icon="pi pi-undo" size="small" text rounded severity="warn" @click="doCancel(slotProps.data.id)" />
            <Button v-if="canBypass && slotProps.data.current_approver_id" icon="pi pi-forward" size="small" text rounded severity="warn" @click="openBypass(slotProps.data)" v-tooltip.top="'强制跳过'" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Approve dialog -->
    <Dialog v-model:visible="approveDialog" header="审批通过" :modal="true" :style="{ width: '24rem' }">
      <Textarea v-model="comment" class="w-full" rows="3" placeholder="审批意见（可选）" />
      <template #footer>
        <Button label="取消" severity="secondary" @click="approveDialog = false" />
        <Button label="确认通过" @click="doApprove" />
      </template>
    </Dialog>

    <!-- Reject dialog -->
    <Dialog v-model:visible="rejectDialog" header="审批驳回" :modal="true" :style="{ width: '24rem' }">
      <Textarea v-model="comment" class="w-full" rows="3" placeholder="驳回原因" />
      <template #footer>
        <Button label="取消" severity="secondary" @click="rejectDialog = false" />
        <Button label="确认驳回" severity="danger" @click="doReject" />
      </template>
    </Dialog>

    <!-- Bypass dialog -->
    <Dialog v-model:visible="bypassDialog" header="强制跳过审批" :modal="true" :style="{ width: '28rem' }">
      <div class="flex flex-col gap-3">
        <p class="text-sm text-stone-600">您正在强制跳过审批节点，此操作将记录到审计日志。</p>
        <label class="form-label">跳过原因（必填）</label>
        <Textarea v-model="bypassReason" class="w-full" rows="3" placeholder="请填写强制跳过原因" />
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="bypassDialog = false" />
        <Button label="确认跳过" severity="warn" :disabled="!bypassReason.trim()" @click="doBypass" />
      </template>
    </Dialog>
  </div>
</template>
