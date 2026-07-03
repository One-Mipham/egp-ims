<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listInvSales, createInvSale, updateInvSale, deleteInvSale, listInventory } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const products = ref<any[]>([])
const items = ref<any[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

const searchText = ref('')
const filterStatus = ref('')
const startDate = ref('')
const endDate = ref('')
const page = ref(1)
const pageSize = 20

const emptyForm = () => ({
  company_id: companyId,
  order_no: '',
  customer_name: '',
  order_date: '',
  product_name: '',
  quantity: 0,
  unit: '个',
  unit_price: 0,
  total_amount: 0,
  cost_amount: 0,
  status: '待出库',
  notes: '',
})

const form = ref(emptyForm())
const statusOptions = ['待出库', '已出库', '已取消']

function autoCalc() {
  const f = form.value
  f.total_amount = parseFloat((f.quantity * f.unit_price).toFixed(2))
  f.cost_amount = f.cost_amount || 0
}

async function load() {
  const params: Record<string, any> = { limit: pageSize, offset: (page.value - 1) * pageSize }
  if (searchText.value) params.search = searchText.value
  if (filterStatus.value) params.status = filterStatus.value
  if (startDate.value) params.start_date = startDate.value
  if (endDate.value) params.end_date = endDate.value
  const { data } = await listInvSales(companyId, params)
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
  autoCalc()
  if (isEdit.value && editId.value) {
    await updateInvSale(editId.value, form.value)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createInvSale(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除？')) {
    await deleteInvSale(id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await load()
  }
}

function exportCSV() {
  const header = ['销售单号', '客户', '产品', '数量', '单位', '单价', '金额', '成本', '毛利', '状态', '日期']
  const rows = items.value.map((i: any) => [
    i.order_no,
    i.customer_name,
    i.product_name,
    i.quantity,
    i.unit,
    i.unit_price,
    i.total_amount,
    i.cost_amount,
    i.profit,
    i.status,
    i.order_date,
  ])
  const csv = [
    header.join(','),
    ...rows.map((r: any[]) => r.map((c: any) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')),
  ].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '销售单.csv'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  const r = await listInventory(companyId)
  products.value = r.data
  await load()
})
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">销售管理</h1>
      <div class="flex gap-2">
        <button @click="exportCSV" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">导出CSV</button>
        <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
          + 新增销售单
        </button>
      </div>
    </div>

    <div class="flex gap-2 mb-3 flex-wrap">
      <input
        v-model="searchText"
        @input="page = 1; load()"
        placeholder="搜索单号/客户/产品..."
        class="border rounded px-2 py-1 text-sm w-56"
      />
      <select
        v-model="filterStatus"
        @change="page = 1; load()"
        class="border rounded px-2 py-1 text-sm"
      >
        <option value="">全部状态</option>
        <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
      </select>
      <input
        type="date"
        v-model="startDate"
        @change="page = 1; load()"
        class="border rounded px-2 py-1 text-sm"
        title="开始日期"
      />
      <span class="text-xs text-zinc-400 self-center">至</span>
      <input
        type="date"
        v-model="endDate"
        @change="page = 1; load()"
        class="border rounded px-2 py-1 text-sm"
        title="结束日期"
      />
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">销售单号</th>
          <th class="p-2 border">客户</th>
          <th class="p-2 border">产品</th>
          <th class="p-2 border text-right">数量</th>
          <th class="p-2 border text-right">单价</th>
          <th class="p-2 border text-right">金额</th>
          <th class="p-2 border text-right">毛利</th>
          <th class="p-2 border">状态</th>
          <th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border font-mono text-xs">{{ item.order_no }}</td>
          <td class="p-2 border">{{ item.customer_name }}</td>
          <td class="p-2 border">{{ item.product_name }}</td>
          <td class="p-2 border text-right">{{ item.quantity }} {{ item.unit }}</td>
          <td class="p-2 border text-right">{{ (item.unit_price || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.total_amount || 0).toLocaleString() }}</td>
          <td
            class="p-2 border text-right font-bold"
            :class="(item.profit || 0) >= 0 ? 'text-green-600' : 'text-red-600'"
          >
            {{ (item.profit || 0).toLocaleString() }}
          </td>
          <td class="p-2 border">{{ item.status }}</td>
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
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑销售单' : '新增销售单' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500">销售单号</label
            ><input v-model="form.order_no" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">客户</label
            ><input v-model="form.customer_name" list="customer-list" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">销售日期</label
            ><input type="date" v-model="form.order_date" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">状态</label>
            <select v-model="form.status" class="w-full border rounded px-2 py-1 text-sm">
              <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">产品名称</label
            ><input v-model="form.product_name" list="product-list" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">单位</label
            ><input v-model="form.unit" list="unit-list" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">数量</label
            ><input
              type="number"
              v-model.number="form.quantity"
              @input="autoCalc"
              class="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label class="text-xs text-zinc-500">单价</label
            ><input
              type="number"
              v-model.number="form.unit_price"
              @input="autoCalc"
              class="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label class="text-xs text-zinc-500">金额（自动）</label
            ><input
              type="number"
              v-model.number="form.total_amount"
              readonly
              class="w-full border rounded px-2 py-1 text-sm bg-zinc-50"
            />
          </div>
          <div>
            <label class="text-xs text-zinc-500">成本金额</label
            ><input type="number" v-model.number="form.cost_amount" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>

    <datalist id="product-list">
      <option v-for="p in products" :key="p.id" :value="p.name" />
    </datalist>
    <datalist id="customer-list">
      <option v-for="p in products" :key="'c' + p.id" :value="p.name" />
    </datalist>
    <datalist id="unit-list">
      <option v-for="p in products" :key="'u' + p.id" :value="p.unit" />
    </datalist>
  </div>
</template>
