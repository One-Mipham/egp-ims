<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Button from 'primevue/button'
import { listVoucherArchive, batchImportVouchers } from '@/api'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const year = ref(new Date().getFullYear() - 1)
const vouchers = ref<any[]>([])
const loading = ref(false)
const importing = ref(false)
const importResult = ref('')

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await listVoucherArchive(cid, year.value)
    vouchers.value = res.data || []
  } finally {
    loading.value = false
  }
}

function handleFileUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = async ev => {
    try {
      const text = ev.target?.result as string
      const lines = text.trim().split('\n')
      if (lines.length < 2) { alert('CSV 至少需要标题行 + 1 行数据'); return }

      const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
      const idx = (name: string) => headers.findIndex(h => h.includes(name))

      const cid = parseInt(localStorage.getItem('companyId') || '1')
      const vouchers_list: any[] = []
      const voucherMap: Record<string, any> = {}

      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(',').map(c => c.trim().replace(/^"|"$/g, ''))
        if (!cols[0] || cols.length < 3) continue

        const date = cols[idx('日期')] || ''
        const voucher_no = cols[idx('凭证号')] || cols[idx('字号')] || ''
        const voucher_type = cols[idx('类型')] || 'transfer'
        const summary = cols[idx('摘要')] || ''
        const account_code = cols[idx('科目代码')] || cols[idx('科目')] || ''
        const debit = parseFloat(cols[idx('借方金额')] || '0') || 0
        const credit = parseFloat(cols[idx('贷方金额')] || '0') || 0
        const description = cols[idx('分录摘要')] || summary

        const key = `${date}|${voucher_no}`
        if (!voucherMap[key]) {
          const vt = voucher_type.includes('收') ? 'receipt' : voucher_type.includes('付') ? 'payment' : 'transfer'
          voucherMap[key] = {
            company_id: cid, date, voucher_no, voucher_type: vt, summary,
            entries: [] as any[],
          }
          vouchers_list.push(voucherMap[key])
        }
        voucherMap[key].entries.push({ account_code, debit, credit, description })
      }

      importing.value = true
      const res = await batchImportVouchers(vouchers_list)
      importResult.value = `导入成功：${res.data.imported} 张凭证`
      await load()
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || '导入失败')
    } finally {
      importing.value = false
      ;(e.target as HTMLInputElement).value = ''
    }
  }
  reader.readAsText(file)
}

const TYPE_LABELS = computed<Record<string, string>>(() => ({
  receipt: t('accounting.vouchers_page.receipt'),
  payment: t('accounting.vouchers_page.payment'),
  transfer: t('accounting.vouchers_page.transfer'),
}))

onMounted(load)
</script>

<template>
  <div class="max-w-5xl">
    <h2 class="text-lg font-bold mb-1">历史年度记账凭证</h2>
    <p class="text-xs text-zinc-400 mb-4">导入或查看过往年度的历史凭证数据</p>

    <!-- Import section -->
    <div class="bg-white border rounded p-4 mb-4">
      <h3 class="font-bold text-sm mb-2">导入历史凭证</h3>
      <p class="text-xs text-zinc-400 mb-2">
        CSV 格式：日期, 凭证号, 类型, 摘要, 科目代码, 借方金额, 贷方金额, 分录摘要
        <br/>每行一个分录（同一凭证多行自动合并），导入后状态为"已记账"。
      </p>
      <div class="flex gap-2 items-center">
        <label class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm cursor-pointer hover:bg-blue-700">
          {{ importing ? '导入中...' : '选择 CSV 文件' }}
          <input type="file" accept=".csv" @change="handleFileUpload" :disabled="importing" class="hidden" />
        </label>
        <span v-if="importResult" class="text-green-600 text-sm">{{ importResult }}</span>
      </div>
    </div>

    <!-- Year filter + list -->
    <div class="flex gap-2 items-center mb-3">
      <input v-model.number="year" type="number" class="border rounded px-2 py-1.5 text-sm w-24" @change="load" />
      <span class="text-sm text-zinc-500">年度</span>
      <Button :label="t('common.search')" icon="pi pi-search" size="small" text @click="load" />
      <span class="text-xs text-zinc-400 ml-2">共 {{ vouchers.length }} 张凭证</span>
    </div>

    <div class="bg-white border rounded overflow-x-auto">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="border-b bg-stone-50 text-left text-xs text-zinc-500">
            <th class="py-2 px-3">{{ t('accounting.vouchers_page.voucherNo') }}</th>
            <th class="py-2 px-3">{{ t('common.date') }}</th>
            <th class="py-2 px-3">{{ t('common.type') }}</th>
            <th class="py-2 px-3">{{ t('accounting.vouchers_page.summary') }}</th>
            <th class="py-2 px-3 text-right">{{ t('common.amount') }}</th>
            <th class="py-2 px-3">分录数</th>
            <th class="py-2 px-3">{{ t('common.status') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="7" class="py-4 text-center text-zinc-400">{{ t('common.loading') }}</td></tr>
          <tr v-if="!loading && !vouchers.length"><td colspan="7" class="py-4 text-center text-zinc-400">{{ t('common.noData') }}</td></tr>
          <tr v-for="v in vouchers" :key="v.id" class="border-b last:border-b-0 hover:bg-stone-50">
            <td class="py-1.5 px-3 font-mono text-xs">{{ v.voucher_no }}</td>
            <td class="py-1.5 px-3">{{ v.date }}</td>
            <td class="py-1.5 px-3 text-xs">{{ TYPE_LABELS[v.voucher_type] || v.voucher_type }}</td>
            <td class="py-1.5 px-3 max-w-xs truncate">{{ v.summary }}</td>
            <td class="py-1.5 px-3 text-right font-number">{{ v.total_debit?.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</td>
            <td class="py-1.5 px-3 text-xs text-zinc-400">{{ v.entry_count }}</td>
            <td class="py-1.5 px-3"><span class="text-xs px-1.5 py-0.5 rounded" :class="v.status === 'posted' ? 'bg-green-100 text-green-700' : 'bg-zinc-100 text-zinc-600'">{{ v.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
