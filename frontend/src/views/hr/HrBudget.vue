<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import { listBudgets, getBudget, createBudget, updateBudget, type BudgetData } from '@/api/budget'

const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
const currentYear = new Date().getFullYear()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const header = reactive({
  companyName: '',
  preparer: '',
  approver: '',
})

// Budget rows: each row has label, type (manual/auto), and 12-month values
interface BudgetLine {
  label: string
  type: 'section' | 'manual' | 'auto'
  indent?: boolean
}

const budgetLines: BudgetLine[] = [
  { label: '一、薪酬支出', type: 'section' },
  { label: '基本薪酬', type: 'manual' },
  { label: '季度绩效', type: 'manual' },
  { label: '年终奖', type: 'manual' },
  { label: '加班费', type: 'manual' },
  { label: '二、补贴与福利', type: 'section' },
  { label: '手机补贴', type: 'manual' },
  { label: '交通车辆补贴', type: 'manual' },
  { label: '餐费补贴', type: 'manual' },
  { label: '职工宿舍', type: 'manual' },
  { label: '其他补贴', type: 'manual' },
  { label: '三、社保与保险', type: 'section' },
  { label: '五险一金-企业部分', type: 'manual' },
  { label: '五险一金-个人部分', type: 'manual' },
  { label: '商业保险', type: 'manual' },
  { label: '四、招聘与培训', type: 'section' },
  { label: '招聘费用', type: 'manual' },
  { label: '培训费用', type: 'manual' },
  { label: '五、合计', type: 'section' },
  { label: '预算合计', type: 'auto' },
]

// Initialize data for all manual rows
const data = reactive<Record<string, (number | null)[]>>({})
for (const line of budgetLines) {
  if (line.type === 'manual') {
    data[line.label] = Array(12).fill(null)
  }
}

function setValue(label: string, mi: number, val: string) {
  const n = parseFloat(val)
  if (data[label]) data[label][mi] = isNaN(n) ? null : n
}

function annualSum(values: (number | null)[]): number | null {
  if (values.every(v => v == null)) return null
  return values.reduce((a: number, v) => a + (v ?? 0), 0)
}

function fmt(v: number | null): string {
  return v != null ? v.toLocaleString() : ''
}

// Auto-calculate budget total = sum of all manual rows
const budgetTotal = computed(() => {
  const result: (number | null)[] = Array(12).fill(null)
  for (let i = 0; i < 12; i++) {
    let sum = 0
    let hasAny = false
    for (const line of budgetLines) {
      if (line.type === 'manual' && data[line.label]) {
        const v = data[line.label][i]
        if (v != null) {
          sum += v
          hasAny = true
        }
      }
    }
    result[i] = hasAny ? sum : null
  }
  return result
})

function getValue(line: BudgetLine, mi: number): number | null {
  if (line.type === 'auto') return budgetTotal.value[mi]
  if (line.type === 'manual') return data[line.label]?.[mi] ?? null
  return null
}

// ── Short codes for persistence (≤10 chars) ──
const labelToCode: Record<string, string> = {
  基本薪酬: 'sal_base',
  季度绩效: 'sal_perf',
  年终奖: 'sal_year',
  加班费: 'sal_ot',
  手机补贴: 'sub_phone',
  交通车辆补贴: 'sub_car',
  餐费补贴: 'sub_meal',
  职工宿舍: 'sub_dorm',
  其他补贴: 'sub_other',
  '五险一金-企业部分': 'ins5_co',
  '五险一金-个人部分': 'ins5_per',
  商业保险: 'ins_comm',
  招聘费用: 'recruit',
  培训费用: 'train',
}
const codeToLabel = Object.fromEntries(Object.entries(labelToCode).map(([k, v]) => [v, k]))

// ── API persistence ──
const hrBudgetId = ref<number | null>(null)
const saving = ref(false)
const loading = ref(false)
const saveMessage = ref('')

async function saveHrBudget() {
  saving.value = true
  saveMessage.value = ''
  try {
    const items: { account_code: string; month: string; amount: number }[] = []
    for (const [label, values] of Object.entries(data)) {
      const code = labelToCode[label]
      if (!code) continue
      for (let mi = 0; mi < 12; mi++) {
        if (values[mi] != null) {
          items.push({
            account_code: code,
            month: `${currentYear}-${String(mi + 1).padStart(2, '0')}`,
            amount: values[mi]!,
          })
        }
      }
    }
    if (hrBudgetId.value) {
      await updateBudget(hrBudgetId.value, { name: 'HR预算', items })
    } else {
      const res = await createBudget({ company_id: companyId.value, name: 'HR预算', year: currentYear, items })
      hrBudgetId.value = (res.data as BudgetData).id
    }
    saveMessage.value = '保存成功'
  } catch (e: any) {
    saveMessage.value = '保存失败: ' + (e?.response?.data?.detail || e.message)
  } finally {
    saving.value = false
  }
}

async function loadHrBudget() {
  loading.value = true
  try {
    const res = await listBudgets(companyId.value, currentYear)
    for (const b of res.data as BudgetData[]) {
      if (b.name === 'HR预算') {
        hrBudgetId.value = b.id
        const detailR = await getBudget(b.id)
        for (const key of Object.keys(data)) {
          data[key].fill(null)
        }
        for (const item of (detailR.data as BudgetData).items) {
          const label = codeToLabel[item.account_code]
          if (label && data[label]) {
            const mi = parseInt(item.month.slice(5, 7)) - 1
            if (mi >= 0 && mi < 12) data[label][mi] = item.amount
          }
        }
        break
      }
    }
  } catch (_e) {
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHrBudget()
})
</script>

<template>
  <div class="space-y-6">
    <div class="page-header flex items-center justify-between">
      <h2>人力资源预算管理</h2>
      <div class="flex items-center gap-2">
        <span
          v-if="saveMessage"
          class="text-xs"
          :class="saveMessage.includes('失败') ? 'text-red-500' : 'text-green-600'"
          >{{ saveMessage }}</span
        >
        <Button label="加载" size="small" severity="secondary" :loading="loading" @click="loadHrBudget" />
        <Button label="保存" size="small" severity="success" :loading="saving" @click="saveHrBudget" />
      </div>
    </div>

    <!-- Header info -->
    <div class="form-card">
      <div class="grid grid-cols-3 gap-4 mb-4">
        <div>
          <label class="block text-xs text-zinc-500 mb-1">公司名称</label>
          <InputText v-model="header.companyName" class="w-full text-xs" placeholder="输入公司名称" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">编制人</label>
          <InputText v-model="header.preparer" class="w-full text-xs" placeholder="编制人姓名" />
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">审批人</label>
          <InputText v-model="header.approver" class="w-full text-xs" placeholder="审批人姓名" />
        </div>
      </div>
    </div>

    <!-- Budget table -->
    <div class="form-card">
      <h3 class="text-sm font-semibold text-stone-700 mb-2">年度人力资源预算表</h3>

      <div class="table-compact overflow-x-auto">
        <table class="data-table text-xs w-full">
          <thead>
            <tr>
              <th class="w-8 text-center">序号</th>
              <th class="w-36 text-left">项目</th>
              <th v-for="m in months" :key="m" class="w-[64px] text-right">{{ m }}</th>
              <th class="w-[72px] text-right bg-stone-200 font-semibold">全年合计</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(line, idx) in budgetLines" :key="line.label">
              <!-- Section header -->
              <tr v-if="line.type === 'section'" class="bg-amber-50 font-semibold">
                <td class="text-center text-amber-700 text-[10px]">{{ idx }}</td>
                <td class="text-amber-800" colspan="14">{{ line.label }}</td>
              </tr>

              <!-- Data row -->
              <tr
                v-else
                :class="{ 'bg-stone-50 font-semibold': line.type === 'auto', 'bg-white': line.type === 'manual' }"
              >
                <td class="text-center text-stone-400 text-[10px]">{{ line.type === 'auto' ? '' : idx }}</td>
                <td :class="{ 'pl-6': line.indent, 'font-medium': line.type === 'manual' }">{{ line.label }}</td>

                <td v-for="mi in 12" :key="'m' + line.label + mi" class="text-right p-0">
                  <template v-if="line.type === 'manual'">
                    <input
                      type="number"
                      class="w-full text-right px-1 py-1 border border-transparent hover:border-stone-300 focus:border-amber-400 focus:outline-none bg-transparent font-number text-xs"
                      :value="getValue(line, mi) != null ? getValue(line, mi) : ''"
                      @input="(e: Event) => setValue(line.label, mi, (e.target as HTMLInputElement).value)"
                    />
                  </template>
                  <span v-else class="px-1 font-number text-stone-700">
                    {{ fmt(getValue(line, mi)) }}
                  </span>
                </td>

                <td
                  class="text-right font-number font-semibold bg-stone-100 px-1"
                  :class="line.type === 'auto' ? 'text-stone-700' : 'text-stone-400'"
                >
                  {{ fmt(annualSum(line.type === 'auto' ? budgetTotal : data[line.label] || [])) }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
