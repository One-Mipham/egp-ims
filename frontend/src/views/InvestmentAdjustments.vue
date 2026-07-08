<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import { listPositions, listAdjustments, createAdjustment, updateAdjustment, deleteAdjustment } from '@/api'
import { useI18n } from '@/i18n'

const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const { t } = useI18n()

const items = ref<any[]>([])
const positions = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const filterPosition = ref<number | null>(null)

const emptyForm = () => ({
  position_id: null as number | null,
  adjustment_date: '',
  previous_value: 0,
  adjusted_value: 0,
  change_amount: 0,
  reason: '',
})

const form = ref(emptyForm())
const changeAmount = computed(() => (form.value.adjusted_value || 0) - (form.value.previous_value || 0))

function getPositionName(id: number) {
  const p = positions.value.find((p: any) => p.id === id)
  return p ? `${p.security_name} (${p.account_code})` : '-'
}

async function load() {
  loading.value = true
  try {
    const [adjRes, posRes] = await Promise.all([
      listAdjustments(companyId.value, filterPosition.value || undefined),
      listPositions(companyId.value),
    ])
    items.value = adjRes.data
    positions.value = posRes.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = emptyForm()
  isEdit.value = false
  editId.value = null
  showDialog.value = true
}

function openEdit(row: any) {
  form.value = {
    position_id: row.position_id,
    adjustment_date: row.adjustment_date,
    previous_value: row.previous_value,
    adjusted_value: row.adjusted_value,
    change_amount: row.change_amount,
    reason: row.reason || '',
  }
  isEdit.value = true
  editId.value = row.id
  showDialog.value = true
}

async function handleSave() {
  const data = { ...form.value, change_amount: changeAmount.value }
  if (!form.value.position_id || !form.value.adjustment_date) return
  if (isEdit.value && editId.value) {
    await updateAdjustment(editId.value, data)
  } else {
    await createAdjustment(companyId.value, data)
  }
  showDialog.value = false
  await load()
}

async function handleDelete(id: number) {
  if (!confirm('确定删除此公允价值调整记录？关联凭证将一并删除。')) return
  await deleteAdjustment(id)
  await load()
}

function onFilterChange() {
  load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">{{ t('investments.adjustments') }}</h2>
      <Button label="新增调整" icon="pi pi-plus" size="small" @click="openCreate" />
    </div>

    <!-- Filter -->
    <div class="flex items-center gap-3 mb-3">
      <Dropdown
        v-model="filterPosition"
        :options="positions"
        optionLabel="security_name"
        optionValue="id"
        placeholder="按持仓筛选"
        showClear
        class="w-64"
        @change="onFilterChange"
      />
    </div>

    <!-- Table -->
    <DataTable :value="items" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="adjustment_date" header="调整日期" sortable />
      <Column header="持仓">
        <template #body="{ data }">{{ getPositionName(data.position_id) }}</template>
      </Column>
      <Column field="previous_value" header="前值">
        <template #body="{ data }">¥{{ data.previous_value?.toLocaleString() }}</template>
      </Column>
      <Column field="adjusted_value" header="调整值">
        <template #body="{ data }">¥{{ data.adjusted_value?.toLocaleString() }}</template>
      </Column>
      <Column header="变动金额">
        <template #body="{ data }">
          <span :class="data.change_amount >= 0 ? 'text-emerald-600' : 'text-red-500'">
            {{ data.change_amount >= 0 ? '+' : '' }}¥{{ data.change_amount?.toLocaleString() }}
          </span>
        </template>
      </Column>
      <Column field="reason" header="原因" />
      <Column header="凭证">
        <template #body="{ data }">
          <Tag v-if="data.voucher_id" severity="info" :value="String(data.voucher_id)" class="text-xs" />
          <span v-else class="text-stone-300">-</span>
        </template>
      </Column>
      <Column :header="t('common.actions')">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button icon="pi pi-pencil" size="small" severity="secondary" text rounded @click="openEdit(data)" />
            <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Create/Edit Dialog -->
    <Dialog
      v-model:visible="showDialog"
      :header="isEdit ? '编辑调整' : '新增公允价值调整'"
      :style="{ width: '480px' }"
      modal
    >
      <div class="flex flex-col gap-3 pt-2">
        <label class="text-sm text-stone-600">持仓 <span class="text-red-400">*</span></label>
        <Dropdown
          v-model="form.position_id"
          :options="positions"
          optionLabel="security_name"
          optionValue="id"
          placeholder="选择持仓"
          filterable
          :disabled="isEdit"
        />

        <label class="text-sm text-stone-600">调整日期 <span class="text-red-400">*</span></label>
        <InputText v-model="form.adjustment_date" placeholder="YYYY-MM-DD" />

        <div class="flex gap-3">
          <div class="flex-1">
            <label class="text-sm text-stone-600">调整前公允价值</label>
            <InputNumber v-model="form.previous_value" mode="currency" currency="CNY" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="text-sm text-stone-600">调整后公允价值</label>
            <InputNumber v-model="form.adjusted_value" mode="currency" currency="CNY" class="w-full" />
          </div>
        </div>

        <div class="bg-stone-50 rounded p-3 text-center">
          <span class="text-sm text-stone-500">变动金额: </span>
          <span class="text-lg font-bold" :class="changeAmount >= 0 ? 'text-emerald-600' : 'text-red-500'">
            {{ changeAmount >= 0 ? '+' : '' }}¥{{ Math.abs(changeAmount).toLocaleString() }}
          </span>
        </div>

        <label class="text-sm text-stone-600">调整原因</label>
        <Textarea v-model="form.reason" rows="2" placeholder="如：市场价格变动、估值模型调整等" />
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" @click="showDialog = false" />
        <Button
          label="保存并生成凭证"
          @click="handleSave"
          :disabled="!form.position_id || !form.adjustment_date || changeAmount === 0"
        />
      </template>
    </Dialog>
  </div>
</template>
