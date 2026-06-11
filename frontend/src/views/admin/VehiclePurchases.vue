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
import { listVehiclePurchases, createVehiclePurchase, updateVehiclePurchase, deleteVehiclePurchase, submitVehiclePurchase } from '@/api'

const items = ref<any[]>([]); const loading = ref(false); const showDialog = ref(false)
const isEdit = ref(false); const editId = ref<number | null>(null); const companyId = ref(1)
const emptyForm = () => ({ company_id: companyId.value, applicant: '', department: '', vehicle_brand: '', vehicle_model: '', configuration: '', estimated_price: 0, supplier_name: '', supplier_contact: '', reason: '' })
const form = ref(emptyForm())

async function load() { loading.value = true; try { const { data } = await listVehiclePurchases(companyId.value); items.value = data } finally { loading.value = false } }
function openCreate() { form.value = emptyForm(); isEdit.value = false; showDialog.value = true }
function openEdit(row: any) { form.value = { ...row }; isEdit.value = true; editId.value = row.id; showDialog.value = true }
async function save() {
  try {
    if (isEdit.value && editId.value) await updateVehiclePurchase(editId.value, form.value)
    else await createVehiclePurchase(form.value)
    showDialog.value = false; await load()
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
async function remove(id: number) { if (!confirm('确定删除？')) return; try { await deleteVehiclePurchase(id); await load() } catch (e: any) { alert(e.response?.data?.detail || '删除失败') } }
async function doSubmit(id: number) { const ids = prompt('请输入审批人ID（逗号分隔）：'); if (!ids) return; try { await submitVehiclePurchase(id, ids.split(',').map(Number)); await load() } catch (e: any) { alert(e.response?.data?.detail || '提交失败') } }
const statusSeverity = (s: string) => ({ draft: 'secondary', pending_approval: 'warn', approved: 'success', rejected: 'danger', purchased: 'info' } as any)[s] || 'secondary'
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-end mb-4"><Button label="新建采购申请" icon="pi pi-plus" @click="openCreate" /></div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="applicant" header="申请人" sortable />
        <Column field="department" header="部门" sortable />
        <Column field="vehicle_brand" header="品牌" sortable />
        <Column field="vehicle_model" header="型号" sortable />
        <Column field="estimated_price" header="预估价格" sortable />
        <Column header="状态" style="min-width:90px">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column header="操作" style="min-width:160px">
          <template #body="{ data }">
            <Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" />
            <Button v-if="data.status === 'draft'" text size="small" icon="pi pi-send" @click="doSubmit(data.id)" v-tooltip.top="'提交审批'" />
            <Button v-if="data.status === 'draft'" text size="small" icon="pi pi-trash" severity="danger" @click="remove(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>
    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑采购申请' : '新建采购申请'" :style="{ width: '550px' }" :modal="true">
      <div class="grid grid-cols-2 gap-3">
        <div><label class="block text-xs text-zinc-500 mb-1">申请人</label><InputText v-model="form.applicant" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">部门</label><InputText v-model="form.department" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">品牌</label><InputText v-model="form.vehicle_brand" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">型号</label><InputText v-model="form.vehicle_model" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">预估价格</label><InputNumber v-model="form.estimated_price" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">供应商名称</label><InputText v-model="form.supplier_name" class="w-full" /></div>
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">配置要求</label><Textarea v-model="form.configuration" rows="2" class="w-full" /></div>
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">采购理由</label><Textarea v-model="form.reason" rows="2" class="w-full" /></div>
      </div>
      <template #footer><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="save" /></template>
    </Dialog>
  </div>
</template>
