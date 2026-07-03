<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import { listAccounts, bulkSetInitialBalance } from '@/api'

const accounts = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const searchText = ref('')
const filterLevel = ref<number | null>(null)
const filterCategory = ref('')
const edits = ref<Record<string, number>>({})
const savedMessage = ref('')

const CATEGORIES = [
  { label: '全部', value: '' },
  { label: '资产', value: 'asset' },
  { label: '负债', value: 'liability' },
  { label: '权益', value: 'equity' },
  { label: '成本', value: 'cost' },
  { label: '损益', value: 'profit_loss' },
]

const filtered = computed(() => {
  let list = accounts.value
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(a => a.code.includes(q) || a.name.toLowerCase().includes(q))
  }
  if (filterLevel.value) list = list.filter(a => a.level === filterLevel.value)
  if (filterCategory.value) list = list.filter(a => a.category === filterCategory.value)
  return list
})

const summary = computed(() => {
  let asset = 0, liability = 0, equity = 0
  for (const a of accounts.value) {
    const bal = edits.value[a.code] !== undefined ? edits.value[a.code] : (a.initial_balance || 0)
    if (a.category === 'asset') asset += bal
    else if (a.category === 'liability') liability += bal
    else if (a.category === 'equity') equity += bal
  }
  return { asset, liability, equity, balanced: Math.abs(asset - liability - equity) < 0.02 }
})

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await listAccounts(cid)
    accounts.value = res.data || []
    edits.value = {}
    savedMessage.value = ''
  } finally {
    loading.value = false
  }
}

function getEditVal(code: string) {
  if (edits.value[code] !== undefined) return edits.value[code]
  const a = accounts.value.find(x => x.code === code)
  return a?.initial_balance || 0
}

function setEditVal(code: string, val: number | null) {
  edits.value[code] = val || 0
}

async function saveAll() {
  saving.value = true
  savedMessage.value = ''
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const items = Object.entries(edits.value).map(([code, initial_balance]) => ({ code, initial_balance }))
    if (!items.length) return
    await bulkSetInitialBalance(cid, items)
    savedMessage.value = `已保存 ${items.length} 个科目期初余额`
    edits.value = {}
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="max-w-5xl">
    <h2 class="text-lg font-bold mb-1">期初数据</h2>
    <p class="text-xs text-zinc-400 mb-4">录入各科目的初始余额（建账时的期初数据，后续月份自动累计）</p>

    <!-- Summary bar -->
    <div class="flex gap-4 mb-4 text-sm">
      <div class="bg-white border rounded px-3 py-2 flex-1">
        <span class="text-zinc-400">资产合计</span>
        <span class="ml-2 font-bold font-number">{{ summary.asset.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
      </div>
      <div class="bg-white border rounded px-3 py-2 flex-1">
        <span class="text-zinc-400">负债合计</span>
        <span class="ml-2 font-bold font-number">{{ summary.liability.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
      </div>
      <div class="bg-white border rounded px-3 py-2 flex-1">
        <span class="text-zinc-400">权益合计</span>
        <span class="ml-2 font-bold font-number">{{ summary.equity.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
      </div>
      <div class="bg-white border rounded px-3 py-2 flex-1" :class="summary.balanced ? 'border-green-300' : 'border-red-300'">
        <span :class="summary.balanced ? 'text-green-600' : 'text-red-500'" class="text-xs">
          {{ summary.balanced ? '✅ 借贷平衡' : '❌ 不平衡 (资产 ≠ 负债+权益)' }}
        </span>
      </div>
    </div>

    <!-- Filters + actions -->
    <div class="flex gap-2 mb-3 items-center flex-wrap">
      <input v-model="searchText" placeholder="搜索代码/名称..." class="border rounded px-2 py-1.5 text-sm w-44" />
      <select v-model="filterLevel" class="border rounded px-2 py-1.5 text-sm">
        <option :value="null">全部级别</option>
        <option v-for="l in 4" :key="l" :value="l">{{ l }}级</option>
      </select>
      <select v-model="filterCategory" class="border rounded px-2 py-1.5 text-sm">
        <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
      </select>
      <div class="flex-1" />
      <Button label="保存全部" icon="pi pi-save" @click="saveAll" :loading="saving" :disabled="!Object.keys(edits).length" size="small" />
      <span v-if="savedMessage" class="text-green-600 text-xs">{{ savedMessage }}</span>
      <span v-if="Object.keys(edits).length" class="text-amber-600 text-xs">{{ Object.keys(edits).length }} 个科目已修改</span>
    </div>

    <!-- Table -->
    <div class="bg-white border rounded overflow-x-auto">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="border-b bg-stone-50 text-left text-xs text-zinc-500">
            <th class="py-2 px-3">代码</th>
            <th class="py-2 px-3">名称</th>
            <th class="py-2 px-3">级别</th>
            <th class="py-2 px-3">类别</th>
            <th class="py-2 px-3">方向</th>
            <th class="py-2 px-3 text-right">期初余额</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="py-4 text-center text-zinc-400">加载中...</td></tr>
          <tr v-for="a in filtered" :key="a.code" class="border-b last:border-b-0 hover:bg-stone-50">
            <td class="py-1.5 px-3 font-mono text-xs">{{ a.code }}</td>
            <td class="py-1.5 px-3">{{ a.name }}</td>
            <td class="py-1.5 px-3 text-xs text-zinc-400">{{ a.level }}</td>
            <td class="py-1.5 px-3 text-xs">{{ a.category }}</td>
            <td class="py-1.5 px-3 text-xs">{{ a.balance_direction === 'debit' ? '借' : '贷' }}</td>
            <td class="py-1.5 px-3 text-right">
              <InputNumber
                :modelValue="getEditVal(a.code)"
                @update:modelValue="(v: number | null) => setEditVal(a.code, v)"
                mode="currency"
                currency="CNY"
                :minFractionDigits="2"
                :maxFractionDigits="2"
                class="w-36"
                inputClass="text-right text-sm font-number"
                :disabled="a.level < 4 && a.children?.length"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
