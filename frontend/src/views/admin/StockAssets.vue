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
import InputNumber from 'primevue/inputnumber'
import { listStockAssets, createStockAsset, updateStockAsset, deleteStockAsset, listStockCategories } from '@/api'

const { t } = useI18n()

const items = ref<any[]>([])
const categories = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const companyId = ref(1)
const statusFilter = ref('')
const categoryFilter = ref<number | null>(null)
const statuses = ['', '使用中', '闲置', '损坏', '已报废']
const emptyForm = () => ({
  company_id: companyId.value,
  asset_code: '',
  name: '',
  category_id: null,
  brand: '',
  model: '',
  department: '',
  custodian: '',
  location: '',
  purchase_date: '',
  purchase_price: 0,
  status: '使用中',
  quantity: 1,
  notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [r1, r2] = await Promise.all([
      listStockAssets(companyId.value, statusFilter.value || undefined, categoryFilter.value || undefined),
      listStockCategories(companyId.value),
    ])
    items.value = r1.data
    categories.value = r2.data
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
    if (isEdit.value && editId.value) await updateStockAsset(editId.value, form.value)
    else await createStockAsset(form.value)
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.error'))
  }
}
async function remove(id: number) {
  if (!confirm(t('common.deleteConfirm'))) return
  try {
    await deleteStockAsset(id)
    await load()
  } catch (_e: any) {
    alert(t('common.deleteFailed'))
  }
}
onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2">
        <Dropdown v-model="statusFilter" :options="statuses" placeholder="全部状态" @change="load" class="w-24" />
        <Dropdown
          v-model="categoryFilter"
          :options="categories"
          optionLabel="name"
          optionValue="id"
          placeholder="全部类别"
          @change="load"
          class="w-32"
          showClear
        />
      </div>
      <Button label="登记资产" icon="pi pi-plus" @click="openCreate" />
    </div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="15">
        <Column field="asset_code" header="资产编码" sortable />
        <Column field="name" header="资产名称" sortable />
        <Column field="brand" header="品牌" sortable />
        <Column field="department" :header="t('admin.department')" sortable />
        <Column field="custodian" header="保管人" sortable />
        <Column :header="t('common.status')" style="min-width: 80px">
          <template #body="{ data }"
            ><Tag
              :value="data.status"
              :severity="
                data.status === '使用中'
                  ? 'success'
                  : data.status === '损坏'
                    ? 'warn'
                    : data.status === '已报废'
                      ? 'danger'
                      : 'info'
              "
          /></template>
        </Column>
        <Column :header="t('common.actions')" style="min-width: 120px">
          <template #body="{ data }">
            <Button text size="small" icon="pi pi-pencil" @click="openEdit(data)" />
            <Button text size="small" icon="pi pi-trash" severity="danger" @click="remove(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑资产' : '登记资产'"
      :style="{ width: '600px' }"
      :modal="true"
    >
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">资产编码</label
          ><InputText v-model="form.asset_code" class="w-full" />
        </div>
        <div class="col-span-2">
          <label class="block text-xs text-zinc-500 mb-1">资产名称</label
          ><InputText v-model="form.name" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">类别</label
          ><Dropdown
            v-model="form.category_id"
            :options="categories"
            optionLabel="name"
            optionValue="id"
            placeholder="选择类别"
            class="w-full"
            showClear
          />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">品牌</label><InputText v-model="form.brand" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">型号</label><InputText v-model="form.model" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">{{ t('admin.department') }}</label
          ><InputText v-model="form.department" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">保管人</label
          ><InputText v-model="form.custodian" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">位置</label
          ><InputText v-model="form.location" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">购买日期</label
          ><InputText v-model="form.purchase_date" type="date" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">购买价格</label
          ><InputNumber v-model="form.purchase_price" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">数量</label
          ><InputNumber v-model="form.quantity" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">{{ t('common.status') }}</label
          ><Dropdown v-model="form.status" :options="['使用中', '闲置', '损坏', '已报废']" class="w-full" />
        </div>
        <div class="col-span-3">
          <label class="block text-xs text-zinc-500 mb-1">{{ t('common.remark') }}</label
          ><Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer
        ><Button :label="t('common.cancel')" severity="secondary" @click="showDialog = false" /><Button :label="t('common.save')" @click="save"
      /></template>
    </Dialog>
  </div>
</template>
