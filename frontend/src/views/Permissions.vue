<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listAllPermissions, setUserPermissions } from '@/api'

const users = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)

const PERM_FIELDS = [
  { key: 'voucher_create', label: '创建凭证' },
  { key: 'voucher_edit', label: '编辑凭证' },
  { key: 'voucher_delete', label: '删除凭证' },
  { key: 'voucher_post', label: '记账' },
  { key: 'voucher_reverse', label: '反记账' },
  { key: 'period_close', label: '关帐' },
  { key: 'period_unclose', label: '反关帐' },
  { key: 'view_detail_ledger', label: '明细账' },
  { key: 'view_general_ledger', label: '总账' },
  { key: 'view_reports', label: '报表' },
]

const ROLE_LABELS: Record<string, string> = {
  super_admin: '系统管理员', finance_director: '财务总监', finance_manager: '财务经理',
  accountant: '会计', cashier: '出纳', hr_manager: '人事主管',
  admin_staff: '行政专员', department_head: '部门负责人',
}

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await listAllPermissions(cid)
    users.value = res.data || []
  } finally {
    loading.value = false
  }
}

function toggle(user: any, field: string) {
  user.permissions[field] = !user.permissions[field]
}

async function save(user: any) {
  saving.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    await setUserPermissions(user.user_id, { ...user.permissions, user_id: user.user_id, company_id: cid })
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="max-w-6xl">
    <h2 class="text-lg font-bold mb-1">用户权限</h2>
    <p class="text-xs text-zinc-400 mb-4">为每个用户配置细粒度操作权限（管理员可免检）</p>

    <div class="bg-white border rounded overflow-x-auto">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="border-b bg-stone-50 text-left text-xs text-zinc-500">
            <th class="py-2 px-3 sticky left-0 bg-stone-50">用户</th>
            <th class="py-2 px-3">角色</th>
            <th v-for="f in PERM_FIELDS" :key="f.key" class="py-2 px-2 text-center w-16">{{ f.label }}</th>
            <th class="py-2 px-3 w-20">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td :colspan="PERM_FIELDS.length + 4" class="py-4 text-center text-zinc-400">加载中...</td></tr>
          <tr v-for="u in users" :key="u.user_id" class="border-b last:border-b-0 hover:bg-stone-50">
            <td class="py-1.5 px-3 sticky left-0 bg-white">
              <span class="font-medium">{{ u.username }}</span>
              <span v-if="u.is_admin" class="ml-1 text-xs text-amber-500">(管理员)</span>
            </td>
            <td class="py-1.5 px-3 text-xs">{{ ROLE_LABELS[u.role] || u.role }}</td>
            <td v-for="f in PERM_FIELDS" :key="f.key" class="py-1.5 px-2 text-center">
              <input
                type="checkbox"
                :checked="u.permissions[f.key]"
                :disabled="u.is_admin"
                @change="toggle(u, f.key)"
                class="cursor-pointer"
              />
            </td>
            <td class="py-1.5 px-3">
              <button
                v-if="!u.is_admin"
                @click="save(u)"
                :disabled="saving"
                class="text-xs text-blue-600 hover:text-blue-800"
              >保存</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
