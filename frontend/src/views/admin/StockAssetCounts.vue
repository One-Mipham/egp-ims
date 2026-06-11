<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import { listStockCounts, createStockCount, updateStockCount, deleteStockCount, listStockAssets } from '@/api'

const items = ref<any[]>([]); const assets = ref<any[]>([]); const loading = ref(false)
const showDialog = ref(false); const isEdit = ref(false); const editId = ref<number | null>(null)
const companyId = ref(1)
const emptyForm = () => ({ company_id: companyId.value, count_date: new Date().toISOString().slice(0,10), asset_id: 0, book_quantity: 0, actual_quantity: 0, discrepancy: 0, reason: '', counter: '' })
const form = ref(emptyForm())

const discrepancyAuto = computed(() => form.value.actual_quantity - form.value.book_quantity)

async function load() { loading.value = true; try { const [r1, r2] = await Promise.all([listStockCounts(companyId.value), listStockAssets(companyId.value)]); items.value = r1.data; assets.value = r2.data } finally { loading.value = false } }
function openCreate() { form.value = emptyForm(); isEdit.value = false; showDialog.value = true }
function openEdit(r: any) { form.value = { ...r }; isEdit.value = true; editId.value = r.id; showDialog.value = true }
async function save() {
  form.value.discrepancy = discrepancyAuto.value
  try { if (isEdit.value && editId.value) await updateStockCount(editId.value, form.value); else await createStockCount(form.value); showDialog.value = false; await load() }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
async function remove(id: number) { if (!confirm('确定删除？')) return; try { await deleteStockCount(id); await load() } catch (e: any) { alert('删除失败') } }
const assetName = (id: number) => assets.value.find((a: any) => a.id === id)?.name || `资产#${id}`
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-end mb-4"><Button label="新建盘库" icon="pi pi-plus" @click="openCreate" /></div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="count_date" header="盘库日期" sortable />
        <Column header="资产"><template #body="{ data }">{{ assetName(data.asset_id) }}</template></Column>
        <Column field="book_quantity" header="账面数量" />
        <Column field="actual_quantity" header="实盘数量" />
        <Column header="差异" style="min-width:80px"><template #body="{ data }"><span :class="data.discrepancy !== 0 ? 'text-red-600 font-semibold' : ''">{{ data.discrepancy }}</span></template></Column>
        <Column field="counter" header="盘点人" />
        <Column header="操作" style="min-width:120px">
          <template #body="{ data }"><Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" /><Button text size="small" icon="pi pi-trash" severity="danger" @click="remove(data.id)" /></template>
        </Column>
      </DataTable>
    </div>
    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑盘库' : '新建盘库'" :style="{ width: '450px' }" :modal="true">
      <div class="grid gap-3">
        <div><label class="block text-xs text-zinc-500 mb-1">盘库日期</label><InputText v-model="form.count_date" type="date" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">资产</label><Dropdown v-model="form.asset_id" :options="assets" optionLabel="name" optionValue="id" class="w-full" filter /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">账面数量</label><InputNumber v-model="form.book_quantity" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">实盘数量</label><InputNumber v-model="form.actual_quantity" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">差异</label><InputText :model-value="String(discrepancyAuto)" readonly class="w-full" :class="discrepancyAuto !== 0 ? 'text-red-600' : ''" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">盘点人</label><InputText v-model="form.counter" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">差异原因</label><Textarea v-model="form.reason" rows="2" class="w-full" /></div>
      </div>
      <template #footer><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="save" /></template>
    </Dialog>
  </div>
</template>
