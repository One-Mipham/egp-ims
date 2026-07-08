<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useI18n } from '@/i18n'
import {
  listHrPositions,
  createHrPosition,
  updateHrPosition,
  deleteHrPosition,
  listHrPolicies,
  upsertHrPolicy,
} from '@/api'

const { t } = useI18n()

const positions = ref<any[]>([])
const loading = ref(false)
const showPosDialog = ref(false)
const editingPos = ref<any>(null)
const posForm = ref({ name: '', level: 1, sort_order: 0 })
const policyContent = ref('')
const policyTitle = ref('公司人力资源管理制度')
const policySaving = ref(false)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const levelOptions = [
  { label: '1 - 董事会', value: 1 },
  { label: '2 - 监事会', value: 2 },
  { label: '3 - 管理层', value: 3 },
  { label: '4 - 部门正职', value: 4 },
  { label: '5 - 部门副职', value: 5 },
  { label: '6 - 中层', value: 6 },
  { label: '7 - 基层', value: 7 },
]

async function load() {
  loading.value = true
  try {
    const [pr, po] = await Promise.all([listHrPolicies(companyId.value), listHrPositions(companyId.value)])
    positions.value = po.data
    if (pr.data.length > 0) {
      policyContent.value = pr.data[0].content || ''
      policyTitle.value = pr.data[0].title || '公司人力资源管理制度'
    }
  } catch {
    /* */
  } finally {
    loading.value = false
  }
}

async function savePolicy() {
  policySaving.value = true
  try {
    await upsertHrPolicy({ company_id: companyId.value, title: policyTitle.value, content: policyContent.value })
  } finally {
    policySaving.value = false
  }
}

function openAddPos() {
  editingPos.value = null
  posForm.value = { name: '', level: 1, sort_order: positions.value.length }
  showPosDialog.value = true
}
function openEditPos(row: any) {
  editingPos.value = row
  posForm.value = { name: row.name, level: row.level, sort_order: row.sort_order }
  showPosDialog.value = true
}
async function savePos() {
  try {
    if (editingPos.value) {
      await updateHrPosition(editingPos.value.id, { ...posForm.value, company_id: companyId.value })
    } else {
      await createHrPosition({ ...posForm.value, company_id: companyId.value })
    }
    showPosDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.saveFailed'))
  }
}
async function handleDeletePos(id: number) {
  if (!confirm('确定停用此职级？')) return
  await deleteHrPosition(id)
  await load()
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="page-header"><h2>公司人力资源管理制度</h2></div>

    <!-- Policy document -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-3">制度文档</h3>
      <InputText v-model="policyTitle" class="w-full mb-3 text-sm" />
      <Textarea
        v-model="policyContent"
        rows="12"
        class="w-full text-sm font-mono"
        placeholder="在此编写公司人力资源管理制度..."
      />
      <Button label="保存文档" icon="pi pi-check" @click="savePolicy" :loading="policySaving" class="mt-2" />
    </div>

    <!-- Position management -->
    <div class="form-card">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-sm font-semibold text-stone-700">职级数据库</h3>
        <Button label="新增职级" icon="pi pi-plus" size="small" @click="openAddPos" />
      </div>
      <DataTable :value="positions" :loading="loading" stripedRows class="text-xs">
        <Column field="level" header="层级" style="width: 100px">
          <template #body="{ data }">{{
            levelOptions.find(l => l.value === data.level)?.label || data.level
          }}</template>
        </Column>
        <Column field="name" header="职位名称" />
        <Column field="sort_order" header="排序" style="width: 80px" />
        <Column :header="t('common.status')" style="width: 80px">
          <template #body="{ data }">
            <Tag :value="data.is_active ? t('common.enable') : t('common.disable')" :severity="data.is_active ? 'success' : 'danger'" />
          </template>
        </Column>
        <Column :header="t('common.actions')" style="width: 120px">
          <template #body="{ data }">
            <Button label="编辑" text size="small" @click="openEditPos(data)" />
            <Button
              v-if="data.is_active"
              :label="t('common.disable')"
              text
              severity="danger"
              size="small"
              @click="handleDeletePos(data.id)"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showPosDialog" :header="editingPos ? '编辑职级' : '新增职级'" :style="{ width: '400px' }">
      <div class="flex flex-col gap-3 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">职位名称</label
          ><InputText v-model="posForm.name" class="w-full" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">层级</label
          ><Dropdown
            v-model="posForm.level"
            :options="levelOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">排序号</label
          ><InputNumber v-model="posForm.sort_order" class="w-full" />
        </div>
        <Button :label="t('common.save')" icon="pi pi-check" @click="savePos" />
      </div>
    </Dialog>
  </div>
</template>
