<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useI18n } from '@/i18n'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import DatePicker from 'primevue/datepicker'
import {
  type BoardShareholderData,
  listShareholders,
  createShareholder,
  updateShareholder,
  deleteShareholder,
} from '@/api/board'

const { t } = useI18n()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const data = ref<BoardShareholderData[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const shareTypeOptions = [
  { label: '普通股', value: '普通股' },
  { label: '优先股', value: '优先股' },
]

const form = reactive({
  company_id: companyId.value,
  name: '',
  share_type: '普通股',
  share_count: 0,
  share_ratio: 0,
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  entry_date: null as Date | null,
  notes: '',
  status: 'active',
})

function fmtDate(d: Date | null): string {
  if (!d) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function parseDate(s: string | null | undefined): Date | null {
  if (!s) return null
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

async function load() {
  loading.value = true
  try {
    const res = await listShareholders(companyId.value)
    data.value = res.data || []
  } catch {
    /* */
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingId.value = null
  form.company_id = companyId.value
  form.name = ''
  form.share_type = '普通股'
  form.share_count = 0
  form.share_ratio = 0
  form.contact_person = ''
  form.contact_phone = ''
  form.contact_email = ''
  form.entry_date = null
  form.notes = ''
  form.status = 'active'
  showDialog.value = true
}

function openEdit(row: BoardShareholderData) {
  editingId.value = row.id
  form.company_id = row.company_id
  form.name = row.name
  form.share_type = row.share_type
  form.share_count = row.share_count
  form.share_ratio = row.share_ratio
  form.contact_person = row.contact_person || ''
  form.contact_phone = row.contact_phone || ''
  form.contact_email = row.contact_email || ''
  form.entry_date = parseDate(row.entry_date)
  form.notes = row.notes || ''
  form.status = row.status
  showDialog.value = true
}

async function save() {
  saving.value = true
  try {
    if (editingId.value) {
      await updateShareholder(editingId.value, {
        name: form.name,
        share_type: form.share_type,
        share_count: form.share_count,
        share_ratio: form.share_ratio,
        contact_person: form.contact_person || undefined,
        contact_phone: form.contact_phone || undefined,
        contact_email: form.contact_email || undefined,
        entry_date: fmtDate(form.entry_date) || undefined,
        notes: form.notes || undefined,
        status: form.status,
      })
    } else {
      await createShareholder({
        company_id: form.company_id,
        name: form.name,
        share_type: form.share_type,
        share_count: form.share_count,
        share_ratio: form.share_ratio,
        contact_person: form.contact_person || undefined,
        contact_phone: form.contact_phone || undefined,
        contact_email: form.contact_email || undefined,
        entry_date: fmtDate(form.entry_date) || undefined,
        notes: form.notes || undefined,
        status: form.status,
      })
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e?.response?.data?.detail || t('common.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  if (!confirm('确定删除此股东记录？')) return
  await deleteShareholder(id)
  await load()
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="page-header flex items-center justify-between">
      <h2>{{ t('board.shareholders') }}</h2>
      <Button label="新增股东" icon="pi pi-plus" size="small" @click="openAdd" />
    </div>

    <div class="form-card overflow-x-auto">
      <DataTable :value="data" :loading="loading" stripedRows class="text-xs" paginator :rows="15">
        <Column field="name" :header="t('board.shareholderName')" style="min-width: 140px" />
        <Column field="share_type" :header="t('board.shareholderType')" style="width: 100px" />
        <Column field="share_count" header="持股数量" style="width: 100px">
          <template #body="{ data: row }">{{ row.share_count.toLocaleString() }}</template>
        </Column>
        <Column field="share_ratio" :header="t('board.shareRatio')" style="width: 100px">
          <template #body="{ data: row }">{{ row.share_ratio }}%</template>
        </Column>
        <Column field="contact_person" header="联系人" style="width: 90px">
          <template #body="{ data: row }">{{ row.contact_person || '—' }}</template>
        </Column>
        <Column field="contact_phone" header="电话" style="width: 120px">
          <template #body="{ data: row }">{{ row.contact_phone || '—' }}</template>
        </Column>
        <Column field="entry_date" header="入股日期" style="width: 100px">
          <template #body="{ data: row }">{{ row.entry_date || '—' }}</template>
        </Column>
        <Column :header="t('common.status')" style="width: 80px">
          <template #body="{ data: row }">
            <Tag
              :value="row.status === 'active' ? '有效' : '失效'"
              :severity="row.status === 'active' ? 'success' : 'danger'"
            />
          </template>
        </Column>
        <Column :header="t('common.actions')" style="width: 110px">
          <template #body="{ data: row }">
            <Button :label="t('common.edit')" text size="small" @click="openEdit(row)" />
            <Button :label="t('common.delete')" text severity="danger" size="small" @click="handleDelete(row.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog
      v-model:visible="showDialog"
      :header="editingId ? '编辑股东' : '新增股东'"
      :style="{ width: '500px' }"
      modal
    >
      <div class="flex flex-col gap-3 py-4 text-sm">
        <div>
          <label class="text-xs text-zinc-500 mb-1 block">股东名称 *</label>
          <InputText v-model="form.name" class="w-full" required />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">{{ t('board.shareholderType') }}</label>
            <Dropdown
              v-model="form.share_type"
              :options="shareTypeOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">{{ t('common.status') }}</label>
            <Dropdown
              v-model="form.status"
              :options="[
                { label: '有效', value: 'active' },
                { label: '失效', value: 'inactive' },
              ]"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">持股数量</label>
            <InputNumber v-model="form.share_count" :min="0" class="w-full" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">{{ t('board.shareRatio') }} (%)</label>
            <InputNumber v-model="form.share_ratio" :min="0" :max="100" :minFractionDigits="2" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">联系人</label>
            <InputText v-model="form.contact_person" class="w-full" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">电话</label>
            <InputText v-model="form.contact_phone" class="w-full" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">邮箱</label>
            <InputText v-model="form.contact_email" class="w-full" />
          </div>
          <div>
            <label class="text-xs text-zinc-500 mb-1 block">入股日期</label>
            <DatePicker v-model="form.entry_date" date-format="yy-mm-dd" class="w-full" />
          </div>
        </div>

        <div>
          <label class="text-xs text-zinc-500 mb-1 block">{{ t('common.remark') }}</label>
          <Textarea v-model="form.notes" rows="3" class="w-full" />
        </div>

        <Button :label="t('common.save')" icon="pi pi-check" :loading="saving" @click="save" />
      </div>
    </Dialog>
  </div>
</template>
