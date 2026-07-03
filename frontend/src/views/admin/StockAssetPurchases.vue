<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import {
  listStockPurchases,
  createStockPurchase,
  updateStockPurchase,
  deleteStockPurchase,
  submitStockPurchase,
} from '@/api'

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = ref(1)
const emptyForm = () => ({
  company_id: companyId.value,
  applicant: '',
  department: '',
  asset_name: '',
  category: '',
  quantity: 1,
  estimated_price: 0,
  reason: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const { data } = await listStockPurchases(companyId.value)
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
    if (isEdit.value && editId.value) await updateStockPurchase(editId.value, form.value)
    else await createStockPurchase(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}
async function remove(id: number) {
  if (!confirm('确定删除？')) return
  try {
    await deleteStockPurchase(id)
    await load()
  } catch (e: any) {
    alert('删除失败')
  }
}
async function doSubmit(id: number) {
  const ids = prompt('请输入审批人ID（逗号分隔）：')
  if (!ids) return
  try {
    await submitStockPurchase(id, ids.split(',').map(Number))
    await load()
  } catch (e: any) {
    alert('提交失败')
  }
}
const statusSeverity = (s: string) =>
  (({ draft: 'secondary', pending_approval: 'warn', approved: 'success', rejected: 'danger' }) as any)[s] || 'secondary'
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-end mb-4"><Button label="新建采购申请" icon="pi pi-plus" @click="openCreate" /></div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="asset_name" header="资产名称" sortable />
        <Column field="applicant" header="申请人" sortable />
        <Column field="department" header="部门" sortable />
        <Column field="quantity" header="数量" sortable />
        <Column field="estimated_price" header="预估单价" sortable />
        <Column header="状态"
          ><template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template
        ></Column>
        <Column header="操作" style="min-width: 160px">
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
      :header="isEdit ? '编辑采购申请' : '新建采购申请'"
      :style="{ width: '500px' }"
      :modal="true"
    >
      <div class="grid grid-cols-2 gap-3">
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">资产名称</label
          ><InputText v-model="form.asset_name" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">申请人</label
          ><InputText v-model="form.applicant" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">部门</label
          ><InputText v-model="form.department" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">类别</label
          ><InputText v-model="form.category" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">数量</label
          ><InputNumber v-model="form.quantity" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">预估单价</label
          ><InputNumber v-model="form.estimated_price" class="w-full" />
        </div>
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">采购理由</label
          ><Textarea v-model="form.reason" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="save"
      /></template>
    </Dialog>
  </div>
</template>
