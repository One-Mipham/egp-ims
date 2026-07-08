<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import { exportData } from '@/api'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const loading = ref(false)
const selectedTables = ref(['accounts', 'vouchers', 'voucher_entries', 'departments', 'periods'])
const exportFormat = ref('csv')

const TABLE_OPTIONS = [
  { label: '科目表', value: 'accounts' },
  { label: '凭证', value: 'vouchers' },
  { label: '凭证分录', value: 'voucher_entries' },
  { label: '部门', value: 'departments' },
  { label: '会计期间', value: 'periods' },
]

function toggleAll() {
  if (selectedTables.value.length === TABLE_OPTIONS.length) {
    selectedTables.value = []
  } else {
    selectedTables.value = TABLE_OPTIONS.map(t => t.value)
  }
}

async function doExport() {
  if (!selectedTables.value.length) return
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    await exportData(cid, selectedTables.value.join(','), exportFormat.value)
  } catch (e: any) {
    alert(e.response?.data?.detail || '导出失败')
  } finally {
    loading.value = false
  }
}

async function doFullDownload() {
  loading.value = true
  try {
    const { exportFullDb } = await import('@/api')
    await exportFullDb()
  } catch (e: any) {
    alert(e.response?.data?.detail || '下载失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl">
    <h2 class="text-lg font-bold mb-4">{{ t('system.exportData') }}</h2>

    <!-- 按表导出 -->
    <div class="bg-white border rounded p-4 mb-4">
      <h3 class="font-bold text-sm mb-3">按表导出</h3>
      <div class="flex items-center gap-2 mb-3">
        <Checkbox v-model="selectedTables" value="accounts" inputId="t_accounts" />
        <label for="t_accounts" class="text-sm">科目表</label>
        <Checkbox v-model="selectedTables" value="vouchers" inputId="t_vouchers" class="ml-3" />
        <label for="t_vouchers" class="text-sm">凭证</label>
        <Checkbox v-model="selectedTables" value="voucher_entries" inputId="t_entries" class="ml-3" />
        <label for="t_entries" class="text-sm">凭证分录</label>
      </div>
      <div class="flex items-center gap-2 mb-3">
        <Checkbox v-model="selectedTables" value="departments" inputId="t_depts" />
        <label for="t_depts" class="text-sm">部门</label>
        <Checkbox v-model="selectedTables" value="periods" inputId="t_periods" class="ml-3" />
        <label for="t_periods" class="text-sm">会计期间</label>
        <button @click="toggleAll" class="text-xs text-blue-600 ml-3">{{ selectedTables.length === TABLE_OPTIONS.length ? '取消全选' : '全选' }}</button>
      </div>
      <div class="flex gap-2 items-center mb-3">
        <label class="text-sm text-zinc-500">格式：</label>
        <select v-model="exportFormat" class="border rounded px-2 py-1 text-sm">
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
        </select>
      </div>
      <Button label="导出所选表" icon="pi pi-download" @click="doExport" :loading="loading" size="small" />
    </div>

    <!-- 完整数据库 -->
    <div class="bg-white border rounded p-4">
      <h3 class="font-bold text-sm mb-3">完整数据库下载</h3>
      <p class="text-xs text-zinc-400 mb-3">下载当前 SQLite 数据库文件（包含所有公司数据）。</p>
      <Button label="下载完整数据库" icon="pi pi-database" @click="doFullDownload" :loading="loading" severity="secondary" size="small" />
    </div>
  </div>
</template>
