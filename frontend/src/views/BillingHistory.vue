<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import { getBillingHistory, renewSubscription, cancelSubscription } from '@/api/subscriptions'
import { useI18n } from '@/i18n'

const { t } = useI18n()
const subscriptions = ref<any[]>([])
const payments = ref<any[]>([])
const loading = ref(false)
const companyId = parseInt(localStorage.getItem('companyId') || '0')

const STATUS_LABELS: Record<string, string> = {
  trialing: '试用中', active: '已激活', past_due: '已过期', cancelled: '已取消', expired: '已失效',
}
const STATUS_SEVERITY: Record<string, string> = {
  trialing: 'info', active: 'success', past_due: 'warn', cancelled: 'secondary', expired: 'danger',
}

async function load() {
  loading.value = true
  try {
    const res = await getBillingHistory(companyId)
    subscriptions.value = res.data.subscriptions || []
    payments.value = res.data.payments || []
  } catch (_) { /* */ }
  finally { loading.value = false }
}

async function doRenew() {
  if (!confirm('确认续费？')) return
  try {
    await renewSubscription(companyId)
    await load()
    localStorage.setItem('subscriptionStatus', 'active')
    alert('续费成功')
  } catch (e: any) {
    alert(e.response?.data?.detail || '续费失败')
  }
}

async function doCancel() {
  if (!confirm('确认取消订阅？取消后将仅保留知识库访问权限。')) return
  try {
    await cancelSubscription(companyId)
    await load()
    localStorage.setItem('subscriptionStatus', 'cancelled')
    localStorage.setItem('enabledModules', JSON.stringify(['knowledge']))
    alert('已取消订阅')
  } catch (e: any) {
    alert(e.response?.data?.detail || '取消失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-stone-800">订阅与账单</h2>
      <div class="flex gap-2">
        <Button label="续费" icon="pi pi-refresh" size="small" severity="success" @click="doRenew" />
        <Button label="取消订阅" icon="pi pi-times" size="small" severity="danger" text @click="doCancel" />
      </div>
    </div>

    <!-- Subscription history -->
    <div class="bg-white rounded-xl border border-stone-200 overflow-hidden mb-6">
      <div class="px-4 py-3 bg-stone-50 border-b border-stone-200">
        <h3 class="text-sm font-semibold text-stone-700">订阅记录</h3>
      </div>
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-stone-100 text-stone-500 text-xs">
            <th class="text-left px-4 py-2">套餐</th>
            <th class="text-left px-4 py-2">周期</th>
            <th class="text-left px-4 py-2">状态</th>
            <th class="text-left px-4 py-2">开始</th>
            <th class="text-left px-4 py-2">结束</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in subscriptions" :key="s.id" class="border-b border-stone-50 hover:bg-stone-50/50">
            <td class="px-4 py-2.5 font-medium text-stone-700">{{ s.plan_name }}</td>
            <td class="px-4 py-2.5 text-stone-500">{{ s.billing_cycle === 'monthly' ? '月付' : s.billing_cycle === 'annual' ? '年付' : s.billing_cycle === 'lifetime' ? '买断' : s.billing_cycle }}</td>
            <td class="px-4 py-2.5">
              <Badge :value="STATUS_LABELS[s.status] || s.status" :severity="STATUS_SEVERITY[s.status] || 'info'" />
            </td>
            <td class="px-4 py-2.5 text-stone-500 font-mono text-xs">{{ s.period_start?.slice(0, 10) || '-' }}</td>
            <td class="px-4 py-2.5 text-stone-500 font-mono text-xs">{{ s.period_end?.slice(0, 10) || '-' }}</td>
          </tr>
          <tr v-if="!subscriptions.length">
            <td colspan="5" class="px-4 py-8 text-center text-stone-400">暂无记录</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Payment history -->
    <div class="bg-white rounded-xl border border-stone-200 overflow-hidden">
      <div class="px-4 py-3 bg-stone-50 border-b border-stone-200">
        <h3 class="text-sm font-semibold text-stone-700">支付记录</h3>
      </div>
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-stone-100 text-stone-500 text-xs">
            <th class="text-left px-4 py-2">金额</th>
            <th class="text-left px-4 py-2">方式</th>
            <th class="text-left px-4 py-2">状态</th>
            <th class="text-left px-4 py-2">支付时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in payments" :key="p.id" class="border-b border-stone-50 hover:bg-stone-50/50">
            <td class="px-4 py-2.5 font-mono text-stone-700">¥{{ p.amount?.toLocaleString('zh-CN') }} {{ p.currency }}</td>
            <td class="px-4 py-2.5 text-stone-500">{{ p.payment_method }}</td>
            <td class="px-4 py-2.5">
              <Badge :value="p.status" :severity="p.status === 'completed' ? 'success' : p.status === 'pending' ? 'warn' : 'secondary'" />
            </td>
            <td class="px-4 py-2.5 text-stone-500 font-mono text-xs">{{ p.paid_at?.slice(0, 10) || '-' }}</td>
          </tr>
          <tr v-if="!payments.length">
            <td colspan="4" class="px-4 py-8 text-center text-stone-400">暂无记录</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
