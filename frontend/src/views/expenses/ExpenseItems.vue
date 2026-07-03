<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import { listExpenseItems, createExpenseItem, updateExpenseItem } from '@/api/expenses'

const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const items = ref<any[]>([])
const dialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const loading = ref(false)

const form = ref({ code: '', name: '', parent_code: '', tax_rate: 0, is_active: true })

const parentOptions = ref<{ label: string; value: string }[]>([])

const fetchItems = async () => {
  loading.value = true
  try {
    const res = await listExpenseItems(companyId)
    items.value = res.data
    parentOptions.value = res.data
      .filter((i: any) => !i.parent_code)
      .map((i: any) => ({ label: `${i.code} ${i.name}`, value: i.code }))
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEdit.value = false
  form.value = { code: '', name: '', parent_code: '', tax_rate: 0, is_active: true }
  editId.value = null
  dialog.value = true
}

const openEdit = (item: any) => {
  isEdit.value = true
  form.value = {
    code: item.code,
    name: item.name,
    parent_code: item.parent_code || '',
    tax_rate: item.tax_rate || 0,
    is_active: item.is_active,
  }
  editId.value = item.id
  dialog.value = true
}

const save = async () => {
  try {
    const data = {
      company_id: companyId,
      code: form.value.code,
      name: form.value.name,
      parent_code: form.value.parent_code || undefined,
      tax_rate: form.value.tax_rate,
      is_active: form.value.is_active,
    }
    if (isEdit.value && editId.value) {
      await updateExpenseItem(editId.value, data)
      toast.add({ severity: 'success', summary: '已更新', life: 2000 })
    } else {
      await createExpenseItem(data)
      toast.add({ severity: 'success', summary: '已创建', life: 2000 })
    }
    dialog.value = false
    fetchItems()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '保存失败', detail: e.response?.data?.detail || e.message, life: 3000 })
  }
}

onMounted(fetchItems)
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold">7.4 费用项目</h1>
      <Button label="新增费用项目" icon="pi pi-plus" @click="openCreate" />
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" class="text-sm">
        <Column field="code" header="编码" class="font-mono" />
        <Column field="name" header="名称" />
        <Column field="parent_code" header="上级编码" />
        <Column field="tax_rate" header="税率(%)">
          <template #body="slotProps">
            {{ slotProps.data.tax_rate ? (slotProps.data.tax_rate * 100).toFixed(0) : '-' }}
          </template>
        </Column>
        <Column header="操作" style="width: 6rem">
          <template #body="slotProps">
            <Button icon="pi pi-pencil" size="small" text rounded @click="openEdit(slotProps.data)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog
      v-model:visible="dialog"
      :header="isEdit ? '编辑费用项目' : '新增费用项目'"
      :modal="true"
      :style="{ width: '28rem' }"
    >
      <div class="flex flex-col gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">编码 <span class="text-red-500">*</span></label>
          <InputText v-model="form.code" class="w-full" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">名称 <span class="text-red-500">*</span></label>
          <InputText v-model="form.name" class="w-full" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">上级编码</label>
          <Dropdown
            v-model="form.parent_code"
            :options="parentOptions"
            class="w-full"
            showClear
            placeholder="留空为一级项目"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">税率</label>
          <InputNumber
            v-model="form.tax_rate"
            class="w-full"
            :minFractionDigits="2"
            :maxFractionDigits="2"
            suffix="%"
          />
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="dialog = false" />
        <Button label="保存" @click="save" />
      </template>
    </Dialog>
  </div>
</template>
