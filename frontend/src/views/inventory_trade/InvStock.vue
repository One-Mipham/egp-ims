<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import {
  listInvStock,
  createInvStock,
  updateInvStock,
  deleteInvStock,
  listWarehouses,
  listInventoryCategories,
  listUnitsOfMeasure,
} from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const warehouses = ref<any[]>([])
const categories = ref<any[]>([])
const units = ref<any[]>([])
const items = ref<any[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

const searchText = ref('')
const filterCategory = ref('')
const filterWarehouse = ref('')
const lowStockOnly = ref(false)
const page = ref(1)
const pageSize = 20

const emptyForm = () => ({
  company_id: companyId,
  product_code: '',
  product_name: '',
  category: '',
  quantity: 0,
  unit: '个',
  unit_cost: 0,
  total_cost: 0,
  warehouse: '',
  min_stock: 0,
  max_stock: 0,
  notes: '',
})

const form = ref(emptyForm())

async function load() {
  const params: Record<string, any> = { limit: pageSize, offset: (page.value - 1) * pageSize }
  if (searchText.value) params.search = searchText.value
  if (filterCategory.value) params.category = filterCategory.value
  if (filterWarehouse.value) params.warehouse = filterWarehouse.value
  if (lowStockOnly.value) params.low_stock = true
  const { data } = await listInvStock(companyId, params)
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
  form.value.total_cost = parseFloat((form.value.quantity * form.value.unit_cost).toFixed(2))
  if (isEdit.value && editId.value) {
    await updateInvStock(editId.value, form.value)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createInvStock(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除？')) {
    await deleteInvStock(id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await load()
  }
}

function exportCSV() {
  const header = ['产品编码', '产品名称', '类别', '数量', '单位', '单位成本', '总成本', '仓库', '最低库存']
  const rows = items.value.map((i: any) => [
    i.product_code,
    i.product_name,
    i.category,
    i.quantity,
    i.unit,
    i.unit_cost,
    i.total_cost,
    i.warehouse,
    i.min_stock,
  ])
  const csv = [
    header.join(','),
    ...rows.map((r: any[]) => r.map((c: any) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')),
  ].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '库存.csv'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  const [w, c, u] = await Promise.all([
    listWarehouses(companyId),
    listInventoryCategories(companyId),
    listUnitsOfMeasure(companyId),
  ])
  warehouses.value = w.data
  categories.value = c.data
  units.value = u.data
  await load()
})
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">库存管理</h1>
      <div class="flex gap-2">
        <button @click="exportCSV" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">导出CSV</button>
        <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
          + 新增库存
        </button>
      </div>
    </div>

    <div class="flex gap-2 mb-3 flex-wrap">
      <input
        v-model="searchText"
        @input="page = 1; load()"
        placeholder="搜索编码/名称/类别..."
        class="border rounded px-2 py-1 text-sm w-56"
      />
      <input
        v-model="filterCategory"
        @input="page = 1; load()"
        placeholder="类别筛选"
        class="border rounded px-2 py-1 text-sm w-28"
      />
      <input
        v-model="filterWarehouse"
        @input="page = 1; load()"
        placeholder="仓库筛选"
        class="border rounded px-2 py-1 text-sm w-28"
      />
      <label class="flex items-center gap-1 text-sm cursor-pointer">
        <input
          type="checkbox"
          v-model="lowStockOnly"
          @change="page = 1; load()"
        />
        <span class="text-xs">仅低库存</span>
      </label>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">产品编码</th>
          <th class="p-2 border">产品名称</th>
          <th class="p-2 border">类别</th>
          <th class="p-2 border text-right">数量</th>
          <th class="p-2 border text-right">单位成本</th>
          <th class="p-2 border text-right">总成本</th>
          <th class="p-2 border">仓库</th>
          <th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in items"
          :key="item.id"
          class="hover:bg-zinc-50"
          :class="(item.quantity || 0) <= (item.min_stock || 0) ? 'bg-red-50' : ''"
        >
          <td class="p-2 border font-mono text-xs">{{ item.product_code }}</td>
          <td class="p-2 border">{{ item.product_name }}</td>
          <td class="p-2 border">{{ item.category }}</td>
          <td
            class="p-2 border text-right"
            :class="(item.quantity || 0) <= (item.min_stock || 0) ? 'text-red-600 font-bold' : ''"
          >
            {{ item.quantity }} {{ item.unit }}
            <span v-if="(item.quantity || 0) <= (item.min_stock || 0)" class="text-xs text-red-500 ml-1"
              >⚠低于最低库存</span
            >
          </td>
          <td class="p-2 border text-right">{{ (item.unit_cost || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.total_cost || 0).toLocaleString() }}</td>
          <td class="p-2 border">{{ item.warehouse }}</td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-1 text-xs">编辑</button>
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
      <div class="bg-white rounded-lg w-[550px] p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑库存' : '新增库存' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500">产品编码</label
            ><input v-model="form.product_code" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">产品名称</label
            ><input v-model="form.product_name" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">类别</label
            ><input v-model="form.category" list="category-list" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">单位</label
            ><input v-model="form.unit" list="unit-list" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">数量</label
            ><input type="number" v-model.number="form.quantity" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">单位成本</label
            ><input type="number" v-model.number="form.unit_cost" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">仓库</label
            ><input v-model="form.warehouse" list="warehouse-list" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">最低库存</label
            ><input type="number" v-model.number="form.min_stock" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>

    <datalist id="warehouse-list">
      <option v-for="w in warehouses" :key="w.id" :value="w.name" />
    </datalist>
    <datalist id="category-list">
      <option v-for="c in categories" :key="c.id" :value="c.name" />
    </datalist>
    <datalist id="unit-list">
      <option v-for="u in units" :key="u.id" :value="u.unit_name" />
    </datalist>
  </div>
</template>
