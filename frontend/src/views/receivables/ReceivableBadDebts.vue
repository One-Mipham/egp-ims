<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listReceivables, updateReceivable } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const page = ref(1)
const pageSize = 20

const overdueItems = computed(() =>
  items.value.filter((i: any) => i.balance > 0 && (i.status === '坏账' || (i.aging_days || 0) > 90)),
)

const totalBadDebt = computed(() => overdueItems.value.reduce((s: number, i: any) => s + (i.balance || 0), 0))

async function load() {
  const { data } = await listReceivables(companyId, { limit: pageSize, offset: (page.value - 1) * pageSize })
  items.value = data
}

async function markBadDebt(row: any) {
  if (
    !confirm(
      `确定将 "${row.customer_name} - ${row.invoice_no}" 标记为坏账？余额 ${(row.balance || 0).toLocaleString()} 将计提损失。`,
    )
  )
    return
  await updateReceivable(row.id, { ...row, status: '坏账' })
  toast.add({ severity: 'success', summary: '已标记为坏账', life: 2000 })
  await load()
}

async function restoreBadDebt(row: any) {
  await updateReceivable(row.id, { ...row, status: '未收款' })
  toast.add({ severity: 'success', summary: '已恢复', life: 2000 })
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">坏账管理</h1>
      <div class="text-sm">
        <span class="text-zinc-500">坏账余额合计：</span
        ><span class="text-red-600 font-bold text-lg">{{ totalBadDebt.toLocaleString() }}</span>
      </div>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">客户</th>
          <th class="p-2 border">发票号</th>
          <th class="p-2 border text-right">金额</th>
          <th class="p-2 border text-right">余额</th>
          <th class="p-2 border text-right">账龄(天)</th>
          <th class="p-2 border">状态</th>
          <th class="p-2 border">到期日</th>
          <th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in overdueItems"
          :key="item.id"
          class="hover:bg-zinc-50"
          :class="item.status === '坏账' ? 'bg-red-50' : ''"
        >
          <td class="p-2 border">{{ item.customer_name }}</td>
          <td class="p-2 border font-mono text-xs">{{ item.invoice_no }}</td>
          <td class="p-2 border text-right">{{ (item.amount || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold text-red-600">{{ (item.balance || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold text-red-600">{{ item.aging_days }}</td>
          <td class="p-2 border">
            <span :class="item.status === '坏账' ? 'text-red-600 font-bold' : 'text-amber-600'">{{ item.status }}</span>
          </td>
          <td class="p-2 border text-xs">{{ item.due_date }}</td>
          <td class="p-2 border">
            <button v-if="item.status !== '坏账'" @click="markBadDebt(item)" class="text-red-600 text-xs">
              标记坏账
            </button>
            <button v-else @click="restoreBadDebt(item)" class="text-blue-600 text-xs">恢复</button>
          </td>
        </tr>
        <tr v-if="overdueItems.length === 0">
          <td colspan="8" class="p-6 text-center text-green-600 text-sm">无坏账或逾期账款</td>
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
  </div>
</template>
