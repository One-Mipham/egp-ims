<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { listHrEmployees, createHrEmployee, updateHrEmployee, deleteHrEmployee, listHrPositions, listDepartments } from '@/api'

const employees = ref<any[]>([])
const positions = ref<any[]>([])
const departments = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingEmp = ref<any>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const statusFilter = ref<string | null>(null)
const deptFilter = ref<number | null>(null)

const form = ref({
  employee_code: '', name: '', gender: '', birth_date: '', id_card: '', passport: '',
  native_place: '', graduate_school: '', graduate_date: '', major: '',
  career_history: '', expertise: '', mobile: '', personal_email: '', company_email: '',
  emergency_contact: '', home_address: '',
  nationality: '', political_party: '', religion: '', professional_associations: '', certifications: '',
  position_id: null as number | null,
  department_id: null as number | null, status: '在职', hire_date: '',
})

const genderOptions = [{ label: '男', value: '男' }, { label: '女', value: '女' }]
const statusOptions = [{ label: '在职', value: '在职' }, { label: '试用', value: '试用' }, { label: '离职', value: '离职' }]

async function load() {
  loading.value = true
  try {
    const [e, p, d] = await Promise.all([
      listHrEmployees(companyId.value, statusFilter.value || undefined, deptFilter.value || undefined),
      listHrPositions(companyId.value),
      listDepartments(companyId.value),
    ])
    employees.value = e.data; positions.value = p.data; departments.value = d.data
  } finally { loading.value = false }
}

function openAdd() {
  editingEmp.value = null
  form.value = {
    employee_code: '', name: '', gender: '', birth_date: '', id_card: '', passport: '',
    native_place: '', graduate_school: '', graduate_date: '', major: '',
    career_history: '', expertise: '', mobile: '', personal_email: '', company_email: '',
    emergency_contact: '', home_address: '',
    nationality: '', political_party: '', religion: '', professional_associations: '', certifications: '',
    position_id: null, department_id: null,
    status: '在职', hire_date: '',
  }
  showDialog.value = true
}
function openEdit(row: any) {
  editingEmp.value = row
  form.value = { ...row }
  showDialog.value = true
}
async function saveEmp() {
  try {
    const payload = { ...form.value, company_id: companyId.value }
    if (editingEmp.value) {
      await updateHrEmployee(editingEmp.value.id, payload)
    } else {
      await createHrEmployee(payload)
    }
    showDialog.value = false
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '保存失败') }
}
async function handleDelete(id: number) {
  if (!confirm('确定将该员工标记为离职？')) return
  await deleteHrEmployee(id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header"><h2>员工入职管理</h2></div>
    <div class="flex justify-between items-center mb-4 gap-2 flex-wrap">
      <div class="flex gap-2">
        <Dropdown v-model="statusFilter" :options="statusOptions" option-label="label" option-value="value" placeholder="全部状态" class="w-32 text-xs" @change="load" />
        <Dropdown v-model="deptFilter" :options="departments" option-label="name" option-value="id" placeholder="全部部门" class="w-40 text-xs" @change="load" showClear />
      </div>
      <Button label="新增员工" icon="pi pi-plus" @click="openAdd" />
    </div>

    <DataTable :value="employees" :loading="loading" stripedRows class="text-xs" scrollable>
      <Column field="employee_code" header="员工编号" style="width:100px" />
      <Column field="name" header="姓名" style="width:80px" />
      <Column field="gender" header="性别" style="width:50px" />
      <Column header="部门" style="width:100px">
        <template #body="{ data }">{{ departments.find((d: any) => d.id === data.department_id)?.name || '—' }}</template>
      </Column>
      <Column header="职级" style="width:100px">
        <template #body="{ data }">{{ positions.find((p: any) => p.id === data.position_id)?.name || '—' }}</template>
      </Column>
      <Column header="状态" style="width:70px">
        <template #body="{ data }">
          <Tag :value="data.status" :severity="data.status === '在职' ? 'success' : data.status === '试用' ? 'info' : 'danger'" />
        </template>
      </Column>
      <Column field="hire_date" header="入职日期" style="width:100px" />
      <Column field="mobile" header="手机号" style="width:120px" />
      <Column header="操作" style="width:120px">
        <template #body="{ data }">
          <Button label="编辑" text size="small" @click="openEdit(data)" />
          <Button v-if="data.status !== '离职'" label="离职" text severity="danger" size="small" @click="handleDelete(data.id)" />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="editingEmp ? '编辑员工' : '新增员工'" :style="{ width: '720px' }" :maximizable="true">
      <div class="grid grid-cols-2 gap-3 py-4">
        <!-- 基本信息 -->
        <div class="col-span-2 text-xs font-semibold text-amber-700 border-b pb-1 mb-1">基本信息</div>
        <div><label class="block text-xs text-zinc-500 mb-1">员工编号 *</label><InputText v-model="form.employee_code" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">姓名 *</label><InputText v-model="form.name" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">性别</label><Dropdown v-model="form.gender" :options="genderOptions" option-label="label" option-value="value" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">出生日期</label><InputText v-model="form.birth_date" type="date" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">身份证号码</label><InputText v-model="form.id_card" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">护照号码</label><InputText v-model="form.passport" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">籍贯</label><InputText v-model="form.native_place" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">紧急联系人</label><InputText v-model="form.emergency_contact" class="w-full" /></div>
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">家庭住址</label><InputText v-model="form.home_address" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">国籍</label><InputText v-model="form.nationality" class="w-full" placeholder="选填" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">所属党派</label><InputText v-model="form.political_party" class="w-full" placeholder="选填" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">宗教信仰</label><InputText v-model="form.religion" class="w-full" placeholder="选填" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">职业团体会员</label><InputText v-model="form.professional_associations" class="w-full" placeholder="选填" /></div>
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">专业资格证书</label><Textarea v-model="form.certifications" rows="2" class="w-full" placeholder="选填" /></div>

        <!-- 教育背景 -->
        <div class="col-span-2 text-xs font-semibold text-amber-700 border-b pb-1 mb-1">教育背景</div>
        <div><label class="block text-xs text-zinc-500 mb-1">毕业院校</label><InputText v-model="form.graduate_school" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">毕业时间</label><InputText v-model="form.graduate_date" type="date" class="w-full" /></div>
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">所学专业</label><InputText v-model="form.major" class="w-full" /></div>

        <!-- 职业信息 -->
        <div class="col-span-2 text-xs font-semibold text-amber-700 border-b pb-1 mb-1">职业信息</div>
        <div><label class="block text-xs text-zinc-500 mb-1">职级</label><Dropdown v-model="form.position_id" :options="positions" option-label="name" option-value="id" class="w-full" showClear /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">部门</label><Dropdown v-model="form.department_id" :options="departments" option-label="name" option-value="id" class="w-full" showClear /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">状态</label><Dropdown v-model="form.status" :options="statusOptions" option-label="label" option-value="value" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">入职日期</label><InputText v-model="form.hire_date" type="date" class="w-full" /></div>
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">职业履历</label><Textarea v-model="form.career_history" rows="3" class="w-full" /></div>
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">个人专长</label><Textarea v-model="form.expertise" rows="2" class="w-full" /></div>

        <!-- 联系方式 -->
        <div class="col-span-2 text-xs font-semibold text-amber-700 border-b pb-1 mb-1">联系方式</div>
        <div><label class="block text-xs text-zinc-500 mb-1">手机号码</label><InputText v-model="form.mobile" class="w-full" /></div>
        <div><label class="block text-xs text-zinc-500 mb-1">个人邮箱</label><InputText v-model="form.personal_email" class="w-full" /></div>
        <div class="col-span-2"><label class="block text-xs text-zinc-500 mb-1">企业邮箱</label><InputText v-model="form.company_email" class="w-full" /></div>
      </div>
      <Button label="保存" icon="pi pi-check" @click="saveEmp" class="w-full" />
    </Dialog>
  </div>
</template>
