<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import { listStockGifts, createStockGift, updateStockGift, deleteStockGift, listGiftCategories } from '@/api'

const items = ref<any[]>([]); const categories = ref<any[]>([]); const loading = ref(false)
const showDialog = ref(false); const isEdit = ref(false); const editId = ref<number | null>(null)
const companyId = ref(1); const categoryFilter = ref<number | null>(null)
const emptyForm = () => ({ company_id: companyId.value, name: '', category_id: null, unit: '个', current_stock: 0, unit_price: 0 })
const form = ref(emptyForm())

async function load() { loading.value = true; try { const [r1, r2] = await Promise.all([listStockGifts(companyId.value, categoryFilter.value || undefined), listGiftCategories(companyId.value)]); items.value = r1.data; categories.value = r2.data } finally { loading.value = false } }
function openCreate() { form.value = emptyForm(); isEdit.value = false; showDialog.value = true }
function openEdit(r: any) { form.value = { ...r }; isEdit.value = true; editId.value = r.id; showDialog.value = true }
async function save() { try { if (isEdit.value && editId.value) await updateStockGift(editId.value, form.value); else await createStockGift(form.value); showDialog.value = false; await load() } catch (e: any) { alert(e.response?.data?.detail || '操作失败') } }
async function remove(id: number) { if (!confirm('确定删除？')) return; try { await deleteStockGift(id); await load() } catch (e: any) { alert('删除失败') } }
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <Dropdown v-model="categoryFilter" :options="categories" optionLabel="name" optionValue="id" placeholder="全部类别" @change="load" class="w-32" showClear />
      <Button label="新增礼品" icon="pi pi-plus" @click="openCreate" />
    </div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="name" header="礼品名称" sortable />
        <Column field="unit" header="单位" />
        <Column field="current_stock" header="当前库存" sortable>
          <template #body="{ data }"><Tag :value="data.current_stock.toString()" :severity="data.current_stock <= 5 ? 'warn' : data.current_stock === 0 ? 'danger' : 'success'" /></template>
        </Column>
        <Column field="unit_price" header="单价" />
        <Column header="操作" style="min-width:120px">
          <template #body="{ data }"><Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" /><Button text size="small" icon="pi pi-trash" severity="danger" @click="remove(data.id)" /></template>
        </Column>
      </DataTable>
    </div>
    <Dialog v-model:visible="showDialog" :header="isEdit ? '编辑礼品' : '新增礼品'" :style="{ width: '450px' }" :modal="true">
      <div class="grid grid-cols-2 gap-3">
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">名称</label><InputText v-model="form.name" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">类别</label><Dropdown v-model="form.category_id" :options="categories" optionLabel="name" optionValue="id" class="w-full" showClear /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">单位</label><Dropdown v-model="form.unit" :options="['个', '箱', '盒', '套', '件']" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">当前库存</label><InputNumber v-model="form.current_stock" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">单价</label><InputNumber v-model="form.unit_price" class="w-full" /></div>
      </div>
      <template #footer><Button label="取消" severity="secondary" @click="showDialog = false" /><Button label="保存" @click="save" /></template>
    </Dialog>
  </div>
</template>
