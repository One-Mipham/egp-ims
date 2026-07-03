<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Password from 'primevue/password'
import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  changeMyPassword,
  getMe,
  getUserPermissions,
  setUserPermissions,
} from '@/api'

const users = ref<any[]>([])
const me = ref<any>(null)
const loading = ref(false)
const showAddDialog = ref(false)
const showResetDialog = ref(false)
const showChangeOwnDialog = ref(false)
const showPermDialog = ref(false)
const resetTarget = ref<number | null>(null)
const permTarget = ref<any>(null)
const newUser = ref({ username: '', email: '', password: '', role: 'accountant' })
const newOwnPassword = ref({ current: '', new: '' })
const resetPassword = ref('')

const ROLE_LABELS: Record<string, string> = {
  super_admin: '系统管理员',
  finance_director: '财务总监',
  finance_manager: '财务经理',
  accountant: '会计',
  cashier: '出纳',
  hr_manager: '人事主管',
  admin_staff: '行政专员',
  department_head: '部门负责人',
}

const roleOptions = Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))

const PERM_FIELDS = [
  { key: 'voucher_create', label: '创建凭证' },
  { key: 'voucher_edit', label: '编辑凭证' },
  { key: 'voucher_delete', label: '删除凭证' },
  { key: 'voucher_post', label: '记账' },
  { key: 'voucher_reverse', label: '反记账' },
  { key: 'period_close', label: '结账' },
  { key: 'period_unclose', label: '反结账' },
  { key: 'view_detail_ledger', label: '查看明细账' },
  { key: 'view_general_ledger', label: '查看总账' },
  { key: 'view_reports', label: '查看报表' },
]

const permValues = ref<Record<string, boolean>>({})

async function load() {
  loading.value = true
  try {
    const [res, meRes] = await Promise.all([listUsers(), getMe()])
    users.value = res.data
    me.value = meRes.data
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!newUser.value.username || !newUser.value.password) return
  try {
    await createUser(newUser.value)
    showAddDialog.value = false
    newUser.value = { username: '', email: '', password: '', role: 'accountant' }
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '创建失败')
  }
}

function handleReset(userId: number) {
  resetTarget.value = userId
  resetPassword.value = ''
  showResetDialog.value = true
}

async function confirmReset() {
  if (!resetTarget.value || !resetPassword.value) return
  try {
    await resetUserPassword(resetTarget.value, resetPassword.value)
    showResetDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '重置失败')
  }
}

async function handleToggleActive(user: any) {
  try {
    await updateUser(user.id, { is_active: !user.is_active })
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(user: any) {
  if (!confirm(`确定删除用户 ${user.username}？`)) return
  try {
    await deleteUser(user.id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

async function handleChangeOwnPassword() {
  if (!newOwnPassword.value.current || !newOwnPassword.value.new) return
  try {
    await changeMyPassword(newOwnPassword.value.current, newOwnPassword.value.new)
    showChangeOwnDialog.value = false
    newOwnPassword.value = { current: '', new: '' }
  } catch (e: any) {
    alert(e.response?.data?.detail || '修改失败')
  }
}

async function openPermissions(user: any) {
  permTarget.value = user
  const companyId = localStorage.getItem('companyId')
  if (!companyId) return
  try {
    const res = await getUserPermissions(user.id, Number(companyId))
    const data = res.data
    for (const f of PERM_FIELDS) {
      permValues.value[f.key] = !!data[f.key]
    }
  } catch {
    for (const f of PERM_FIELDS) {
      permValues.value[f.key] = false
    }
  }
  showPermDialog.value = true
}

async function savePermissions() {
  const companyId = localStorage.getItem('companyId')
  if (!permTarget.value || !companyId) return
  try {
    await setUserPermissions(permTarget.value.id, {
      user_id: permTarget.value.id,
      company_id: Number(companyId),
      ...Object.fromEntries(PERM_FIELDS.map(f => [f.key, permValues.value[f.key] || false])),
    })
    showPermDialog.value = false
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存权限失败')
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2">
        <Button
          label="修改我的密码"
          icon="pi pi-key"
          severity="secondary"
          size="small"
          @click="showChangeOwnDialog = true"
        />
        <Button label="新增用户" icon="pi pi-plus" @click="showAddDialog = true" />
      </div>
    </div>
    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto max-w-fit min-w-full">
      <DataTable :value="users" :loading="loading" stripedRows class="shadow-sm" tableStyle="min-width: auto">
        <Column field="username" header="用户名" sortable style="width: 120px" />
        <Column field="email" header="邮箱" style="width: 180px" />
        <Column header="角色" style="width: 100px">
          <template #body="{ data }">
            {{ ROLE_LABELS[data.role] || data.role }}
          </template>
        </Column>
        <Column header="状态" style="width: 70px">
          <template #body="{ data }">
            <Tag :value="data.is_active ? '启用' : '停用'" :severity="data.is_active ? 'success' : 'danger'" />
          </template>
        </Column>
        <Column header="最后登录" style="width: 155px">
          <template #body="{ data }">
            <span class="text-xs text-stone-400">{{
              data.last_login ? new Date(data.last_login).toLocaleString('zh-CN') : '—'
            }}</span>
          </template>
        </Column>
        <Column header="操作" style="width: 230px">
          <template #body="{ data }">
            <Button
              v-if="data.is_active"
              label="停用"
              text
              severity="danger"
              size="small"
              @click="handleToggleActive(data)"
            />
            <Button v-else label="启用" text severity="success" size="small" @click="handleToggleActive(data)" />
            <Button label="重置密码" text severity="info" size="small" @click="handleReset(data.id)" />
            <Button label="权限" text severity="info" size="small" @click="openPermissions(data)" />
            <Button
              v-if="data.is_active"
              label="删除"
              text
              severity="danger"
              size="small"
              @click="handleDelete(data)"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Add user dialog -->
    <Dialog v-model:visible="showAddDialog" header="新增用户" :style="{ width: '450px' }">
      <div class="flex flex-col gap-4 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">用户名 *</label>
          <InputText v-model="newUser.username" class="w-full" placeholder="登录用户名" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">邮箱</label>
          <InputText v-model="newUser.email" class="w-full" type="email" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">密码 *</label>
          <Password v-model="newUser.password" class="w-full" toggle-mask />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">角色</label>
          <Dropdown
            v-model="newUser.role"
            :options="roleOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <Button label="创建" icon="pi pi-check" @click="handleAdd" />
      </div>
    </Dialog>

    <!-- Reset password dialog -->
    <Dialog v-model:visible="showResetDialog" header="重置密码" :style="{ width: '400px' }">
      <div class="flex flex-col gap-4 py-4">
        <p class="text-sm text-zinc-600 tracking-wide">为该用户设置新密码</p>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">新密码</label>
          <Password v-model="resetPassword" class="w-full" toggle-mask />
        </div>
        <Button label="确认重置" icon="pi pi-key" @click="confirmReset" :disabled="!resetPassword" />
      </div>
    </Dialog>

    <!-- Change own password dialog -->
    <Dialog v-model:visible="showChangeOwnDialog" header="修改我的密码" :style="{ width: '400px' }">
      <div class="flex flex-col gap-4 py-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">当前密码</label>
          <Password v-model="newOwnPassword.current" class="w-full" toggle-mask :feedback="false" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1 tracking-wider uppercase">新密码</label>
          <Password v-model="newOwnPassword.new" class="w-full" toggle-mask />
        </div>
        <Button
          label="确认修改"
          icon="pi pi-check"
          @click="handleChangeOwnPassword"
          :disabled="!newOwnPassword.current || !newOwnPassword.new"
        />
      </div>
    </Dialog>

    <!-- Permissions dialog -->
    <Dialog v-model:visible="showPermDialog" header="用户权限管理" :style="{ width: '450px' }">
      <div class="flex flex-col gap-3 py-4">
        <p class="text-sm text-zinc-600 tracking-wide">
          为 <span class="font-medium text-zinc-800">{{ permTarget?.username }}</span
          >（{{ ROLE_LABELS[permTarget?.role] || permTarget?.role }}）设置细粒度权限
        </p>
        <div class="grid grid-cols-2 gap-2">
          <div v-for="f in PERM_FIELDS" :key="f.key" class="flex items-center gap-2">
            <input
              type="checkbox"
              :id="'perm-' + f.key"
              v-model="permValues[f.key]"
              class="w-3.5 h-3.5 rounded border-zinc-300 text-emerald-700 focus:ring-emerald-600"
            />
            <label :for="'perm-' + f.key" class="text-xs text-zinc-700 cursor-pointer select-none">{{ f.label }}</label>
          </div>
        </div>
        <div class="flex gap-2 pt-2">
          <Button label="保存" icon="pi pi-check" @click="savePermissions" />
          <Button label="取消" icon="pi pi-times" severity="secondary" @click="showPermDialog = false" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
