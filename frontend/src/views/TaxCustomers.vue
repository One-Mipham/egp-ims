<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import { listCounterparties } from '@/api'
import api from '@/api'

const customers = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const searchText = ref('')
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const emptyForm = () => ({
  name: '', short_name: '', tax_number: '', bank_account: '',
  bank_name: '', address: '', phone: '', contact_person: '',
  website: '', email: '', zip_code: '', category: '客户',
})
const form = ref(emptyForm())

const filteredCustomers = computed(() => {
  if (!searchText.value) return customers.value
  const q = searchText.value.toLowerCase()
  return customers.value.filter((c: any) =>
    (c.name || '').includes(q) || (c.tax_number || '').includes(q) ||
    (c.code || '').includes(q) || (c.contact_person || '').includes(q)
  )
})

async function load() {
  loading.value = true
  try {
    const res = await listCounterparties(companyId.value)
    customers.value = res.data
  } finally { loading.value = false }
}

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    name: row.name || '', short_name: row.short_name || '',
    tax_number: row.tax_number || '', bank_account: row.bank_account || '',
    bank_name: row.bank_name || '', address: row.address || '',
    phone: row.phone || '', contact_person: row.contact_person || '',
    website: row.website || '', email: row.email || '',
    zip_code: row.zip_code || '', category: row.category || '客户',
  }
  showDialog.value = true
}

async function handleSave(saveAndNew: boolean) {
  if (!form.value.name) return
  saving.value = true
  try {
    if (editingId.value) {
      await api.put(`/counterparties/${editingId.value}`, form.value)
    } else {
      await api.post('/counterparties/', form.value, { params: { company_id: companyId.value } })
    }
    if (saveAndNew) {
      form.value = emptyForm()
      editingId.value = null
    } else {
      showDialog.value = false
    }
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}

async function handleDelete(id: number) {
  if (!confirm('确认停用该客户？')) return
  try {
    await api.delete(`/counterparties/${id}`)
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '删除失败') }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2">
        <InputText v-model="searchText" placeholder="搜索客户名称/税号/编码..." class="w-64" />
      </div>
      <Button label="新增客户" icon="pi pi-plus" @click="openAdd" />
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="filteredCustomers" :loading="loading" stripedRows paginator :rows="15" class="shadow-sm" tableStyle="min-width: auto">
        <Column header="序号" style="width:60px">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column field="code" header="编码" style="width:80px" />
        <Column field="name" header="客户名称" style="width:180px" />
        <Column field="tax_number" header="税号" style="width:140px" />
        <Column field="bank_name" header="开户银行" style="width:140px" />
        <Column field="bank_account" header="银行账号" style="width:150px" />
        <Column field="contact_person" header="联系人" style="width:80px" />
        <Column field="phone" header="电话" style="width:110px" />
        <Column header="操作" style="width:120px">
          <template #body="{ data }">
            <Button label="编辑" text severity="info" size="small" @click="openEdit(data)" />
            <Button label="停用" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑客户' : '新增客户'" :style="{ width: '700px' }">
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">客户名称 *</label>
            <InputText v-model="form.name" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">简称</label>
            <InputText v-model="form.short_name" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税号</label>
            <InputText v-model="form.tax_number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">电话</label>
            <InputText v-model="form.phone" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">开户银行</label>
            <InputText v-model="form.bank_name" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">银行账号</label>
            <InputText v-model="form.bank_account" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">联系人</label>
            <InputText v-model="form.contact_person" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">网站</label>
            <InputText v-model="form.website" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">邮箱</label>
            <InputText v-model="form.email" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">邮编</label>
            <InputText v-model="form.zip_code" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">地址</label>
          <InputText v-model="form.address" class="w-full" />
        </div>
        <div class="flex gap-2">
          <Button label="保存" icon="pi pi-check" @click="handleSave(false)" :loading="saving" />
          <Button label="保存新增" icon="pi pi-plus" severity="secondary" @click="handleSave(true)" :loading="saving" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
