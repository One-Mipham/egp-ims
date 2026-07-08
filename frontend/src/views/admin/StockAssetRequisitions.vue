<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from '@/i18n'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import {
  listStockRequisitions,
  createStockRequisition,
  updateStockRequisition,
  deleteStockRequisition,
  submitStockRequisition,
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
  asset_id: null,
  applicant: '',
  department: '',
  quantity: 1,
  reason: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const { data } = await listStockRequisitions(companyId.value)
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
function openEdit(r: any) {
  form.value = { ...r }
  isEdit.value = true
  editId.value = r.id
  showDialog.value = true
}
async function save() {
  try {
    if (isEdit.value && editId.value) await updateStockRequisition(editId.value, form.value)
    else await createStockRequisition(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.error'))
  }
}
async function remove(id: number) {
  if (!confirm(t('common.deleteConfirm'))) return
  try {
    await deleteStockRequisition(id)
    await load()
  } catch (_e: any) {
    alert(t('common.deleteFailed'))
  }
}
async function doSubmit(id: number) {
  const ids = prompt('请输入审批人ID（逗号分隔）：')
  if (!ids) return
  try {
    await submitStockRequisition(id, ids.split(',').map(Number))
    await load()
  } catch (_e: any) {
    alert('提交失败')
  }
}
const statusSeverity = (s: string) =>
  (({ draft: 'secondary', pending_approval: 'warn', approved: 'success', rejected: 'danger' }) as any)[s] || 'secondary'
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-end mb-4"><Button label="新建领用申请" icon="pi pi-plus" @click="openCreate" /></div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="applicant" header="申请人" sortable />
        <Column field="department" :header="t('admin.department')" sortable />
        <Column field="quantity" header="数量" />
        <Column :header="t('common.status')"
          ><template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template
        ></Column>
        <Column :header="t('common.actions')" style="min-width: 160px">
          <template #body="{ data }">
            <Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" />
            <Button v-if="data.status === 'draft'" text size="small" icon="pi pi-send" @click="doSubmit(data.id)" />
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
      :header="isEdit ? '编辑领用申请' : '新建领用申请'"
      :style="{ width: '450px' }"
      :modal="true"
    >
      <div class="grid gap-3">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">资产ID</label
          ><InputNumber v-model="form.asset_id" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">申请人</label
          ><InputText v-model="form.applicant" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">{{ t('admin.department') }}</label
          ><InputText v-model="form.department" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">数量</label
          ><InputNumber v-model="form.quantity" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">领用理由</label
          ><Textarea v-model="form.reason" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button :label="t('common.cancel')" severity="secondary" @click="showDialog = false" /><Button :label="t('common.save')" @click="save"
      /></template>
    </Dialog>
  </div>
</template>
