<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from '@/i18n'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import {
  listAdminDocuments,
  createAdminDocument,
  updateAdminDocument,
  deleteAdminDocument,
  submitDocument,
  issueDocument,
} from '@/api'

const { t } = useI18n()

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = ref(1)

const emptyForm = () => ({
  company_id: companyId.value,
  title: '',
  document_number: '',
  issuing_department: '',
  recipient_departments: '',
  priority: '普通',
  content: '',
  attachment_path: '',
  applicant_id: 1,
  applicant_name: '管理员',
})
const form = ref(emptyForm())

const priorities = ['普通', '紧急', '特急']
const statusFilter = ref('')

async function load() {
  loading.value = true
  try {
    const { data } = await listAdminDocuments(companyId.value, statusFilter.value || undefined)
    items.value = data
  } finally {
    loading.value = false
  }
}
function openCreate() {
  form.value = emptyForm()
  isEdit.value = false
  showDialog.value = true
}
function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true
  editId.value = row.id
  showDialog.value = true
}
async function save() {
  try {
    if (isEdit.value && editId.value) await updateAdminDocument(editId.value, form.value)
    else await createAdminDocument(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.error'))
  }
}
async function remove(id: number) {
  if (!confirm(t('common.deleteConfirm'))) return
  try {
    await deleteAdminDocument(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.deleteFailed'))
  }
}
async function doSubmit(id: number) {
  const ids = prompt('请输入审批人ID（逗号分隔，如 2,3）：')
  if (!ids) return
  try {
    await submitDocument(id, ids.split(',').map(Number))
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '提交失败')
  }
}
async function doIssue(id: number) {
  if (!confirm('确认下发此文件？')) return
  try {
    await issueDocument(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '下发失败')
  }
}

const statusSeverity = (s: string) => {
  const m: Record<string, string> = {
    draft: 'secondary',
    pending_approval: 'warn',
    approved: 'success',
    rejected: 'danger',
    issued: 'info',
  }
  return m[s] || 'secondary'
}
const prioritySeverity = (p: string) => (p === '特急' ? 'danger' : p === '紧急' ? 'warn' : 'info')

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center">
        <Dropdown
          v-model="statusFilter"
          :options="['', 'draft', 'pending_approval', 'approved', 'rejected', 'issued']"
          placeholder="全部状态"
          @change="load"
          class="w-32"
        />
      </div>
      <Button label="新建文件" icon="pi pi-plus" @click="openCreate" />
    </div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="title" header="文件标题" sortable />
        <Column field="document_number" header="文号" sortable style="min-width: 100px" />
        <Column field="issuing_department" header="发文部门" sortable style="min-width: 100px" />
        <Column field="priority" header="优先级" sortable style="min-width: 80px">
          <template #body="{ data }"
            ><Tag :value="data.priority" :severity="prioritySeverity(data.priority)"
          /></template>
        </Column>
        <Column field="status" :header="t('common.status')" sortable style="min-width: 90px">
          <template #body="{ data }"
            ><Tag
              :value="
                data.status === 'draft'
                  ? '草稿'
                  : data.status === 'pending_approval'
                    ? '审批中'
                    : data.status === 'approved'
                      ? '已审批'
                      : data.status === 'rejected'
                        ? '已驳回'
                        : data.status === 'issued'
                          ? '已下发'
                          : data.status
              "
              :severity="statusSeverity(data.status)"
          /></template>
        </Column>
        <Column :header="t('common.actions')" style="min-width: 200px">
          <template #body="{ data }">
            <Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" />
            <Button
              v-if="data.status === 'draft'"
              text
              size="small"
              icon="pi pi-send"
              @click="doSubmit(data.id)"
              v-tooltip.top="'提交审批'"
            />
            <Button
              v-if="data.status === 'approved'"
              text
              size="small"
              icon="pi pi-check-circle"
              severity="success"
              @click="doIssue(data.id)"
              v-tooltip.top="'下发'"
            />
            <Button
              v-if="data.status === 'draft'"
              text
              size="small"
              icon="pi pi-trash"
              severity="danger"
              @click="remove(data.id)"
            />
          </template>
        </Column>
      </DataTable>
    </div>
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑文件' : '新建文件'"
      :style="{ width: '600px' }"
      :modal="true"
    >
      <div class="grid grid-cols-2 gap-3">
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">文件标题</label
          ><InputText v-model="form.title" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">文号</label
          ><InputText v-model="form.document_number" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">优先级</label
          ><Dropdown v-model="form.priority" :options="priorities" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">发文部门</label
          ><InputText v-model="form.issuing_department" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">收文部门</label
          ><InputText v-model="form.recipient_departments" class="w-full" />
        </div>
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">文件内容</label
          ><Textarea v-model="form.content" rows="4" class="w-full" />
        </div>
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">附件路径</label
          ><InputText v-model="form.attachment_path" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="showDialog = false" />
        <Button :label="t('common.save')" @click="save" />
      </template>
    </Dialog>
  </div>
</template>
