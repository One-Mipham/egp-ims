<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { listContracts, getContractCategories, getContractStats } from '@/api/contracts'
import { listDepartments } from '@/api'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'

const router = useRouter()
const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')

const items = ref<any[]>([])
const loading = ref(false)
const stats = ref<any>(null)

const fType = ref<string>('')
const fCategory = ref<string[]>([])
const fDept = ref<number[]>([])
const fStatus = ref<string>('')
const fSearch = ref('')

const departments = ref<any[]>([])
const categories = ref<string[]>([])

const typeOptions = [
  { label: '供应商合同', value: 'supplier' },
  { label: '客户合同', value: 'customer' },
  { label: '劳动合同', value: 'labor' },
  { label: '租赁合同', value: 'lease' },
]
const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '履行中', value: 'active' },
  { label: '已完成', value: 'completed' },
  { label: '已终止', value: 'terminated' },
]
const statusLabels: Record<string, string> = {
  draft: '草稿',
  active: '履行中',
  completed: '已完成',
  terminated: '已终止',
}
const statusSeverity: Record<string, string> = {
  draft: 'secondary',
  active: 'success',
  completed: 'info',
  terminated: 'danger',
}

async function loadRefs() {
  try {
    const [deptRes, catRes] = await Promise.all([listDepartments(companyId), getContractCategories()])
    departments.value = deptRes.data.map((d: any) => ({ label: d.name, value: d.id }))
    categories.value = catRes.data
  } catch (_) {}
}

async function load() {
  loading.value = true
  try {
    const params: any = { company_id: companyId }
    if (fType.value) params.contract_type = fType.value
    if (fCategory.value.length) params.contract_category = fCategory.value.join(',')
    if (fDept.value.length) params.department_id = fDept.value.join(',')
    if (fStatus.value) params.status = fStatus.value
    if (fSearch.value) params.search = fSearch.value
    const [listRes, statsRes] = await Promise.all([listContracts(params), getContractStats(companyId)])
    items.value = listRes.data
    stats.value = statsRes.data
  } catch (e: any) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e.message, life: 3000 })
  } finally {
    loading.value = false
  }
}

function fmtDate(v: string) {
  if (!v) return ''
  return v.length === 10 ? v : v.slice(0, 10)
}

onMounted(async () => {
  await loadRefs()
  load()
})
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-xl font-bold mb-4">合同查询统计</h1>

    <!-- Stats Cards -->
    <div v-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <template #content>
          <div class="text-center">
            <div class="text-sm text-gray-500">合同总数</div>
            <div class="text-2xl font-bold text-blue-600">{{ stats.total_count }}</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="text-center">
            <div class="text-sm text-gray-500">合同总金额</div>
            <div class="text-2xl font-bold text-green-600">¥{{ stats.total_amount?.toLocaleString() }}</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="text-center">
            <div class="text-sm text-gray-500">履行中</div>
            <div class="text-2xl font-bold text-emerald-600">{{ stats.by_status?.active || 0 }}</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="text-center">
            <div class="text-sm text-gray-500">即将到期</div>
            <div class="text-2xl font-bold text-orange-600">{{ stats.by_status?.completed || 0 }}</div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Stats Detail -->
    <div v-if="stats" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <Card>
        <template #title><div class="text-sm font-semibold">按合同大类</div></template>
        <template #content>
          <div
            v-for="(v, k) in stats.by_type"
            :key="k"
            class="flex justify-between text-sm py-1 border-b last:border-0"
          >
            <span>{{ { supplier: '供应商', customer: '客户', labor: '劳动', lease: '租赁' }[k] || k }}</span>
            <span class="font-medium">{{ v.count }} 份 / ¥{{ v.amount?.toLocaleString() }}</span>
          </div>
        </template>
      </Card>
      <Card>
        <template #title><div class="text-sm font-semibold">按合同类别</div></template>
        <template #content>
          <div
            v-for="(v, k) in stats.by_category"
            :key="k"
            class="flex justify-between text-sm py-1 border-b last:border-0"
          >
            <span>{{ k }}</span>
            <span class="font-medium">{{ v.count }} 份</span>
          </div>
        </template>
      </Card>
      <Card>
        <template #title><div class="text-sm font-semibold">按发起部门</div></template>
        <template #content>
          <div
            v-for="(v, k) in stats.by_department"
            :key="k"
            class="flex justify-between text-sm py-1 border-b last:border-0"
          >
            <span>{{ k }}</span>
            <span class="font-medium">{{ v.count }} 份</span>
          </div>
        </template>
      </Card>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-4 items-center">
      <Dropdown v-model="fType" :options="typeOptions" placeholder="合同大类" class="w-40" showClear @change="load" />
      <MultiSelect
        v-model="fCategory"
        :options="categories"
        placeholder="合同类别"
        class="w-56"
        display="chip"
        @change="load"
      />
      <MultiSelect
        v-model="fDept"
        :options="departments"
        placeholder="发起部门"
        class="w-48"
        display="chip"
        @change="load"
      />
      <Dropdown v-model="fStatus" :options="statusOptions" placeholder="状态" class="w-36" showClear @change="load" />
      <InputText v-model="fSearch" placeholder="搜索..." class="w-48" @keyup.enter="load" />
      <Button icon="pi pi-search" severity="secondary" @click="load" />
    </div>

    <DataTable
      :value="items"
      :loading="loading"
      paginator
      :rows="15"
      :rowsPerPageOptions="[15, 30, 50]"
      stripedRows
      sortField="id"
      :sortOrder="-1"
    >
      <Column field="contract_type" header="大类" style="min-width: 90px">
        <template #body="{ data }">
          <Tag
            :value="
              ({ supplier: '供应商', customer: '客户', labor: '劳动', lease: '租赁' } as Record<string, string>)[
                data.contract_type
              ] || data.contract_type
            "
            severity="info"
          />
        </template>
      </Column>
      <Column field="contract_no" header="合同号码" style="min-width: 140px" sortable />
      <Column field="contract_name" header="合同名称" style="min-width: 160px" sortable />
      <Column field="contract_category" header="类别" style="min-width: 110px" sortable />
      <Column field="party_b" header="乙方" style="min-width: 140px" sortable />
      <Column field="amount" header="金额" style="min-width: 100px" sortable>
        <template #body="{ data }">¥{{ data.amount?.toLocaleString() }}</template>
      </Column>
      <Column field="sign_date" header="签署日期" style="min-width: 100px" sortable>
        <template #body="{ data }">{{ fmtDate(data.sign_date) }}</template>
      </Column>
      <Column field="end_date" header="到期日期" style="min-width: 100px" sortable>
        <template #body="{ data }">{{ fmtDate(data.end_date) }}</template>
      </Column>
      <Column field="status" header="状态" style="min-width: 80px">
        <template #body="{ data }">
          <Tag :value="statusLabels[data.status] || data.status" :severity="statusSeverity[data.status]" />
        </template>
      </Column>
      <Column header="操作" style="min-width: 100px">
        <template #body="{ data }">
          <Button
            icon="pi pi-print"
            severity="secondary"
            size="small"
            @click="router.push(`/finance/contracts/print/${data.id}`)"
            v-tooltip.top="'打印'"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>
