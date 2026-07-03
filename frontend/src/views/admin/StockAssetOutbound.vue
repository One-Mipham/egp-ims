<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import {
  listStockOutbound,
  createStockOutbound,
  updateStockOutbound,
  deleteStockOutbound,
  submitStockOutbound,
  listStockAssets,
} from '@/api'

const items = ref<any[]>([])
const assets = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = ref(1)
const emptyForm = () => ({
  company_id: companyId.value,
  asset_id: 0,
  outbound_type: '领用',
  quantity: 1,
  recipient: '',
  outbound_date: new Date().toISOString().slice(0, 10),
  notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [r1, r2] = await Promise.all([listStockOutbound(companyId.value), listStockAssets(companyId.value)])
    items.value = r1.data
    assets.value = r2.data
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
    if (isEdit.value && editId.value) await updateStockOutbound(editId.value, form.value)
    else await createStockOutbound(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}
async function remove(id: number) {
  if (!confirm('确定删除？')) return
  try {
    await deleteStockOutbound(id)
    await load()
  } catch (e: any) {
    alert('删除失败')
  }
}
async function doSubmit(id: number) {
  const ids = prompt('请输入审批人ID（逗号分隔）：')
  if (!ids) return
  try {
    await submitStockOutbound(id, ids.split(',').map(Number))
    await load()
  } catch (e: any) {
    alert('提交失败')
  }
}
const assetName = (id: number) => assets.value.find((a: any) => a.id === id)?.name || `资产#${id}`
const statusSeverity = (s: string) =>
  (({ draft: 'secondary', pending_approval: 'warn', approved: 'success', completed: 'info' }) as any)[s] || 'secondary'
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-end mb-4"><Button label="新建出库" icon="pi pi-plus" @click="openCreate" /></div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column header="资产"
          ><template #body="{ data }">{{ assetName(data.asset_id) }}</template></Column
        >
        <Column field="outbound_type" header="出库类型" />
        <Column field="quantity" header="数量" />
        <Column field="recipient" header="领用人" />
        <Column field="outbound_date" header="出库日期" sortable />
        <Column header="状态"
          ><template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template
        ></Column>
        <Column header="操作" style="min-width: 160px">
          <template #body="{ data }"
            ><Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" /><Button
              v-if="data.status === 'draft'"
              text
              size="small"
              icon="pi pi-send"
              @click="doSubmit(data.id)" /><Button
              v-if="data.status === 'draft'"
              text
              size="small"
              icon="pi pi-trash"
              severity="danger"
              @click="remove(data.id)"
          /></template>
        </Column>
      </DataTable>
    </div>
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑出库' : '新建出库'"
      :style="{ width: '450px' }"
      :modal="true"
    >
      <div class="grid gap-3">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">资产</label
          ><Dropdown
            v-model="form.asset_id"
            :options="assets"
            optionLabel="name"
            optionValue="id"
            placeholder="选择资产"
            class="w-full"
            filter
          />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">出库类型</label
          ><Dropdown v-model="form.outbound_type" :options="['领用', '调拨', '报废出库']" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">数量</label
          ><InputNumber v-model="form.quantity" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">领用人</label
          ><InputText v-model="form.recipient" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">出库日期</label
          ><InputText v-model="form.outbound_date" type="date" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">备注</label
          ><Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="save"
      /></template>
    </Dialog>
  </div>
</template>
