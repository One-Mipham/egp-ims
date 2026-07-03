<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listFixedAssets, createFixedAsset, updateFixedAsset, deleteFixedAsset } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

const searchText = ref('')
const filterCategory = ref('')
const filterStatus = ref('')
const filterLocation = ref('')
const page = ref(1)
const pageSize = 20

const emptyForm = () => ({
  company_id: companyId,
  asset_code: '',
  name: '',
  category: '设备',
  acquisition_date: '',
  original_value: 0,
  residual_value: 0,
  useful_life: 5,
  depreciation_method: '直线法',
  monthly_depreciation: 0,
  status: '使用中',
  location: '',
  department_id: null,
  notes: '',
})

const form = ref(emptyForm())
const categoryOptions = ['设备', '车辆', '房产', '家具', '电子设备', '软件', '其他']
const statusOptions = ['使用中', '已处置', '报废', '闲置']

async function load() {
  const params: Record<string, any> = { limit: pageSize, offset: (page.value - 1) * pageSize }
  if (searchText.value) params.search = searchText.value
  if (filterCategory.value) params.category = filterCategory.value
  if (filterStatus.value) params.status = filterStatus.value
  if (filterLocation.value) params.location = filterLocation.value
  const { data } = await listFixedAssets(companyId, params)
  items.value = data
}

function openCreate() {
  form.value = emptyForm()
  isEdit.value = false
  editId.value = null
  dialogVisible.value = true
}

function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true
  editId.value = row.id
  dialogVisible.value = true
}

async function save() {
  if (isEdit.value && editId.value) {
    const payload: Record<string, any> = {}
    for (const [k, v] of Object.entries(form.value)) {
      if (
        v !== undefined &&
        k !== 'company_id' &&
        k !== 'id' &&
        k !== 'created_at' &&
        k !== 'updated_at' &&
        k !== 'accumulated_depreciation' &&
        k !== 'net_value' &&
        k !== 'disposal_date' &&
        k !== 'disposal_proceeds' &&
        k !== 'disposal_gain_loss' &&
        k !== 'disposal_reason'
      ) {
        payload[k] = v
      }
    }
    await updateFixedAsset(editId.value, payload)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createFixedAsset(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除该资产？')) {
    await deleteFixedAsset(id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await load()
  }
}

function exportCSV() {
  const header = ['资产编号', '名称', '类别', '原值', '累计折旧', '净值', '状态', '存放地点']
  const rows = items.value.map((i: any) => [
    i.asset_code,
    i.name,
    i.category,
    i.original_value,
    i.accumulated_depreciation,
    i.net_value,
    i.status,
    i.location,
  ])
  const csv = [
    header.join(','),
    ...rows.map((r: any[]) => r.map((c: any) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')),
  ].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '固定资产台账.csv'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">资产台账</h1>
      <div class="flex gap-2">
        <button @click="exportCSV" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">导出CSV</button>
        <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
          + 新增资产
        </button>
      </div>
    </div>

    <div class="flex gap-2 mb-3">
      <input
        v-model="searchText"
        @input="page = 1; load()"
        placeholder="搜索名称/编号..."
        class="border rounded px-2 py-1 text-sm w-48"
      />
      <select
        v-model="filterCategory"
        @change="page = 1; load()"
        class="border rounded px-2 py-1 text-sm"
      >
        <option value="">全部类别</option>
        <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
      </select>
      <select
        v-model="filterStatus"
        @change="page = 1; load()"
        class="border rounded px-2 py-1 text-sm"
      >
        <option value="">全部状态</option>
        <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">资产编号</th>
          <th class="p-2 border">名称</th>
          <th class="p-2 border">类别</th>
          <th class="p-2 border text-right">原值</th>
          <th class="p-2 border text-right">累计折旧</th>
          <th class="p-2 border text-right">净值</th>
          <th class="p-2 border">状态</th>
          <th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border font-mono text-xs">{{ item.asset_code }}</td>
          <td class="p-2 border">{{ item.name }}</td>
          <td class="p-2 border text-xs">{{ item.category }}</td>
          <td class="p-2 border text-right">{{ (item.original_value || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.accumulated_depreciation || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.net_value || 0).toLocaleString() }}</td>
          <td class="p-2 border">
            <span :class="item.status === '使用中' ? 'text-green-600' : 'text-red-500'">{{ item.status }}</span>
          </td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-2 text-xs">编辑</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="flex items-center justify-between mt-3">
      <span class="text-xs text-zinc-400">第 {{ page }} 页</span>
      <div class="flex gap-1">
        <button
          @click="page = Math.max(1, page - 1); load()"
          :disabled="page <= 1"
          class="px-3 py-1 border rounded text-sm disabled:opacity-30"
        >
          上一页
        </button>
        <button
          @click="page = page + 1; load()"
          class="px-3 py-1 border rounded text-sm"
        >
          下一页
        </button>
      </div>
    </div>

    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[600px] max-h-[80vh] overflow-auto p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑资产' : '新增资产' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500">资产编号</label
            ><input v-model="form.asset_code" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">名称</label
            ><input v-model="form.name" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">类别</label>
            <select v-model="form.category" class="w-full border rounded px-2 py-1 text-sm">
              <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">状态</label>
            <select v-model="form.status" class="w-full border rounded px-2 py-1 text-sm">
              <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">购置日期</label
            ><input type="date" v-model="form.acquisition_date" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">存放地点</label
            ><input v-model="form.location" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">原值</label
            ><input
              type="number"
              v-model.number="form.original_value"
              class="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label class="text-xs text-zinc-500">残值</label
            ><input
              type="number"
              v-model.number="form.residual_value"
              class="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label class="text-xs text-zinc-500">使用年限(年)</label
            ><input type="number" v-model.number="form.useful_life" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">折旧方法</label>
            <select v-model="form.depreciation_method" class="w-full border rounded px-2 py-1 text-sm">
              <option value="直线法">直线法</option>
              <option value="双倍余额递减法">双倍余额递减法</option>
              <option value="年数总和法">年数总和法</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">月折旧额（参考值）</label
            ><input
              type="number"
              v-model.number="form.monthly_depreciation"
              class="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
        </div>
        <div class="mt-3">
          <label class="text-xs text-zinc-500">备注</label
          ><textarea v-model="form.notes" class="w-full border rounded px-2 py-1 text-sm" rows="2"></textarea>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
