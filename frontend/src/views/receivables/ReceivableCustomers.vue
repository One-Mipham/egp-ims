<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listReceivables, createReceivable, updateReceivable, deleteReceivable, createReceivablePayment, listReceivableCounterparties } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const counterparties = ref<any[]>([])
const dialogVisible = ref(false)
const paymentDialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const selectedItem = ref<any>(null)
const paymentAmount = ref(0)

const searchText = ref('')
const filterStatus = ref('')
const startDate = ref('')
const endDate = ref('')
const page = ref(1)
const pageSize = 20

const emptyForm = () => ({
  company_id: companyId, customer_name: '', invoice_no: '', invoice_date: '',
  amount: 0, due_date: '', notes: '',
})

const form = ref(emptyForm())
const statusOptions = ['未收款', '部分收款', '已收款', '坏账']

async function load() {
  const params: Record<string, any> = { limit: pageSize, offset: (page.value - 1) * pageSize }
  if (searchText.value) params.search = searchText.value
  if (filterStatus.value) params.status = filterStatus.value
  if (startDate.value) params.start_date = startDate.value
  if (endDate.value) params.end_date = endDate.value
  const { data } = await listReceivables(companyId, params)
  items.value = data
}

function openCreate() {
  form.value = emptyForm()
  isEdit.value = false; editId.value = null
  dialogVisible.value = true
}

function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true; editId.value = row.id
  dialogVisible.value = true
}

async function save() {
  if (isEdit.value && editId.value) {
    await updateReceivable(editId.value, form.value)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createReceivable(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除？')) {
    await deleteReceivable(id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await load()
  }
}

function openPayment(row: any) {
  selectedItem.value = row
  paymentAmount.value = row.balance
  paymentDialogVisible.value = true
}

async function submitPayment() {
  await createReceivablePayment({
    company_id: companyId, receivable_id: selectedItem.value.id,
    payment_date: new Date().toISOString().slice(0, 10),
    amount: paymentAmount.value, payment_method: '银行转账',
  })
  toast.add({ severity: 'success', summary: '收款已登记', life: 2000 })
  paymentDialogVisible.value = false
  await load()
}

function exportCSV() {
  const header = ['客户名称', '发票号', '发票日期', '金额', '已收金额', '余额', '账龄(天)', '状态', '到期日']
  const rows = items.value.map((i: any) => [i.customer_name, i.invoice_no, i.invoice_date || '', i.amount, i.received_amount, i.balance, i.aging_days, i.status, i.due_date || ''])
  const csv = [header.join(','), ...rows.map((r: any[]) => r.map((c: any) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(','))].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = '客户应收管理.csv'; a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  const { data } = await listReceivableCounterparties(companyId)
  counterparties.value = data
  await load()
})
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">客户应收管理</h1>
      <div class="flex gap-2">
        <button @click="exportCSV" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">导出CSV</button>
        <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">+ 新增应收</button>
      </div>
    </div>

    <div class="flex gap-2 mb-3 flex-wrap">
      <input v-model="searchText" @input="page=1; load()" placeholder="搜索客户/发票号..." class="border rounded px-2 py-1 text-sm w-56" />
      <select v-model="filterStatus" @change="page=1; load()" class="border rounded px-2 py-1 text-sm">
        <option value="">全部状态</option>
        <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
      </select>
      <input type="date" v-model="startDate" @change="page=1; load()" class="border rounded px-2 py-1 text-sm" title="开始日期" />
      <span class="text-xs text-zinc-400 self-center">至</span>
      <input type="date" v-model="endDate" @change="page=1; load()" class="border rounded px-2 py-1 text-sm" title="结束日期" />
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">客户</th><th class="p-2 border">发票号</th><th class="p-2 border">发票日期</th>
          <th class="p-2 border text-right">金额</th><th class="p-2 border text-right">已收</th><th class="p-2 border text-right">余额</th>
          <th class="p-2 border text-right">账龄(天)</th><th class="p-2 border">状态</th><th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border">{{ item.customer_name }}</td>
          <td class="p-2 border font-mono text-xs">{{ item.invoice_no }}</td>
          <td class="p-2 border text-xs">{{ item.invoice_date }}</td>
          <td class="p-2 border text-right">{{ (item.amount || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.received_amount || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold" :class="(item.balance || 0) > 0 ? 'text-red-600' : 'text-green-600'">{{ (item.balance || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right" :class="(item.aging_days || 0) > 90 ? 'text-red-600' : ''">{{ item.aging_days }}</td>
          <td class="p-2 border">{{ item.status }}</td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-1 text-xs">编辑</button>
            <button @click="openPayment(item)" v-if="(item.balance || 0) > 0" class="text-green-600 mr-1 text-xs">收款</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="flex items-center justify-between mt-3">
      <span class="text-xs text-zinc-400">第 {{ page }} 页</span>
      <div class="flex gap-1">
        <button @click="page = Math.max(1, page - 1); load()" :disabled="page <= 1" class="px-3 py-1 border rounded text-sm disabled:opacity-30">上一页</button>
        <button @click="page = page + 1; load()" class="px-3 py-1 border rounded text-sm">下一页</button>
      </div>
    </div>

    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[500px] p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑应收' : '新增应收' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs text-zinc-500">客户名称</label><input v-model="form.customer_name" list="counterparty-list" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">发票号</label><input v-model="form.invoice_no" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">发票日期</label><input type="date" v-model="form.invoice_date" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">到期日</label><input type="date" v-model="form.due_date" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">金额</label><input type="number" v-model.number="form.amount" class="w-full border rounded px-2 py-1 text-sm" /></div>
        </div>
        <div class="mt-3"><label class="text-xs text-zinc-500">备注</label><textarea v-model="form.notes" rows="2" class="w-full border rounded px-2 py-1 text-sm"></textarea></div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>

    <div v-if="paymentDialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[400px] p-6">
        <h2 class="text-lg font-bold mb-4">登记收款 - {{ selectedItem?.customer_name }}</h2>
        <p class="text-sm text-zinc-500 mb-3">发票号：{{ selectedItem?.invoice_no }} | 余额：{{ (selectedItem?.balance || 0).toLocaleString() }}</p>
        <div><label class="text-xs text-zinc-500">收款金额</label><input type="number" v-model.number="paymentAmount" class="w-full border rounded px-2 py-1 text-sm" /></div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="paymentDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="submitPayment" class="px-4 py-1.5 bg-green-600 text-white rounded text-sm">确认收款</button>
        </div>
      </div>
    </div>

    <datalist id="counterparty-list">
      <option v-for="cp in counterparties" :key="cp.id" :value="cp.name" />
    </datalist>
  </div>
</template>
