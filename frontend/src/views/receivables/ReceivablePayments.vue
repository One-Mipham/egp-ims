<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listReceivablePayments, createReceivablePayment, listReceivables } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const receivables = ref<any[]>([])
const dialogVisible = ref(false)

const page = ref(1)
const pageSize = 20

const emptyForm = () => ({
  company_id: companyId,
  receivable_id: null as number | null,
  payment_date: new Date().toISOString().slice(0, 10),
  amount: 0,
  payment_method: '银行转账',
  notes: '',
})

const form = ref(emptyForm())

function invoiceLabel(id: number) {
  const r = receivables.value.find((x: any) => x.id === id)
  return r ? `${r.customer_name} · ${r.invoice_no} (余额 ${(r.balance || 0).toLocaleString()})` : `#${id}`
}

async function load() {
  const params = { limit: pageSize, offset: (page.value - 1) * pageSize }
  const [r1, r2] = await Promise.all([
    listReceivablePayments(companyId, params),
    listReceivables(companyId, { limit: 500 }),
  ])
  items.value = r1.data
  receivables.value = r2.data
}

function openCreate() {
  form.value = emptyForm()
  dialogVisible.value = true
}

async function save() {
  await createReceivablePayment(form.value)
  toast.add({ severity: 'success', summary: '收款已登记', life: 2000 })
  dialogVisible.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">收款管理</h1>
      <button @click="openCreate" class="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700">
        + 登记收款
      </button>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">应收发票</th>
          <th class="p-2 border">收款日期</th>
          <th class="p-2 border text-right">金额</th>
          <th class="p-2 border">方式</th>
          <th class="p-2 border text-xs text-zinc-400">备注</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border text-xs">{{ invoiceLabel(item.receivable_id) }}</td>
          <td class="p-2 border text-xs">{{ item.payment_date }}</td>
          <td class="p-2 border text-right font-bold text-green-600">{{ (item.amount || 0).toLocaleString() }}</td>
          <td class="p-2 border text-xs">{{ item.payment_method }}</td>
          <td class="p-2 border text-xs text-zinc-400">{{ item.notes }}</td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="5" class="p-6 text-center text-zinc-400 text-sm">暂无收款记录</td>
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
      <div class="bg-white rounded-lg w-[460px] p-6">
        <h2 class="text-lg font-bold mb-4">登记收款</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-zinc-500">选择发票</label>
            <select v-model.number="form.receivable_id" class="w-full border rounded px-2 py-1.5 text-sm">
              <option :value="null" disabled>-- 请选择 --</option>
              <option v-for="r in receivables" :key="r.id" :value="r.id">
                {{ r.customer_name }} · {{ r.invoice_no }} (余额 {{ (r.balance || 0).toLocaleString() }})
              </option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">收款日期</label
            ><input type="date" v-model="form.payment_date" class="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">金额</label
            ><input type="number" v-model.number="form.amount" class="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">收款方式</label>
            <select v-model="form.payment_method" class="w-full border rounded px-2 py-1.5 text-sm">
              <option>银行转账</option>
              <option>现金</option>
              <option>承兑汇票</option>
              <option>微信/支付宝</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">备注</label
            ><input v-model="form.notes" class="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-green-600 text-white rounded text-sm">确认收款</button>
        </div>
      </div>
    </div>
  </div>
</template>
