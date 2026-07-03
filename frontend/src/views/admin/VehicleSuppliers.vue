<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import { listVehicleSuppliers, createVehicleSupplier, updateVehicleSupplier, deleteVehicleSupplier } from '@/api'

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = ref(1)
const emptyForm = () => ({
  company_id: companyId.value,
  name: '',
  contact_person: '',
  contact_phone: '',
  brands_carried: '',
  notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const { data } = await listVehicleSuppliers(companyId.value)
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
    if (isEdit.value && editId.value) await updateVehicleSupplier(editId.value, form.value)
    else await createVehicleSupplier(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}
async function remove(id: number) {
  if (!confirm('确定删除？')) return
  try {
    await deleteVehicleSupplier(id)
    await load()
  } catch (e: any) {
    alert('删除失败')
  }
}
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-end mb-4"><Button label="新增供应商" icon="pi pi-plus" @click="openCreate" /></div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="name" header="供应商名称" sortable />
        <Column field="contact_person" header="联系人" sortable />
        <Column field="contact_phone" header="联系电话" sortable />
        <Column field="brands_carried" header="代理品牌" />
        <Column header="操作" style="min-width: 120px">
          <template #body="{ data }">
            <Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" />
            <Button text size="small" icon="pi pi-trash" severity="danger" @click="remove(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑供应商' : '新增供应商'"
      :style="{ width: '450px' }"
      :modal="true"
    >
      <div class="grid gap-3">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">名称</label><InputText v-model="form.name" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">联系人</label
          ><InputText v-model="form.contact_person" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">电话</label
          ><InputText v-model="form.contact_phone" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">代理品牌</label
          ><InputText v-model="form.brands_carried" class="w-full" />
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
