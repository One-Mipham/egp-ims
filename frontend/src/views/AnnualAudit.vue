<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Checkbox from 'primevue/checkbox'
import { getAuditReport, saveAuditReport, uploadAuditReportFile, downloadAuditReportFile } from '@/api'

const year = ref(new Date().getFullYear() - 1)
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const found = ref(false)

const form = ref({
  firm_name: '',
  contact_person: '',
  contact_email: '',
  contact_phone: '',
  balance_sheet_ok: false,
  income_statement_ok: false,
  cashflow_statement_ok: false,
  notes: '',
  report_file_name: '',
})

const YEARS = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i)

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await getAuditReport(cid, year.value)
    if (res.data.found && res.data.data) {
      found.value = true
      const d = res.data.data
      form.value = {
        firm_name: d.firm_name || '',
        contact_person: d.contact_person || '',
        contact_email: d.contact_email || '',
        contact_phone: d.contact_phone || '',
        balance_sheet_ok: d.balance_sheet_ok || false,
        income_statement_ok: d.income_statement_ok || false,
        cashflow_statement_ok: d.cashflow_statement_ok || false,
        notes: d.notes || '',
        report_file_name: d.report_file_name || '',
      }
    } else {
      found.value = false
      form.value = {
        firm_name: '', contact_person: '', contact_email: '', contact_phone: '',
        balance_sheet_ok: false, income_statement_ok: false, cashflow_statement_ok: false,
        notes: '', report_file_name: '',
      }
    }
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    await saveAuditReport(cid, year.value, form.value)
    found.value = true
    alert('保存成功')
  } catch (err: any) {
    alert(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleFileUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    await uploadAuditReportFile(cid, year.value, file)
    form.value.report_file_name = file.name
    alert('上传成功')
  } catch (err: any) {
    alert(err.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function handleDownload() {
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    await downloadAuditReportFile(cid, year.value)
  } catch (err: any) {
    alert(err.response?.data?.detail || '下载失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="max-w-3xl">
    <h2 class="text-lg font-bold mb-1">年度审计报告</h2>
    <p class="text-xs text-zinc-400 mb-4">管理各年度的审计机构信息、审计报告文件及三张审定财务报表状态</p>

    <!-- Year selector -->
    <div class="flex gap-2 items-center mb-4">
      <select v-model.number="year" class="border rounded px-2 py-1.5 text-sm" @change="load">
        <option v-for="y in YEARS" :key="y" :value="y">{{ y }} 年</option>
      </select>
      <Button label="查询" icon="pi pi-search" size="small" text @click="load" />
      <span v-if="loading" class="text-xs text-zinc-400">加载中...</span>
    </div>

    <div v-if="!loading" class="bg-white border rounded p-5 space-y-4">
      <!-- 审计机构信息 -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs text-zinc-500 block mb-1">审计机构名称</label>
          <InputText v-model="form.firm_name" class="w-full" placeholder="例如：XX会计师事务所" />
        </div>
        <div>
          <label class="text-xs text-zinc-500 block mb-1">联系人</label>
          <InputText v-model="form.contact_person" class="w-full" placeholder="联系人姓名" />
        </div>
        <div>
          <label class="text-xs text-zinc-500 block mb-1">联系邮箱</label>
          <InputText v-model="form.contact_email" class="w-full" placeholder="email@example.com" />
        </div>
        <div>
          <label class="text-xs text-zinc-500 block mb-1">联系电话</label>
          <InputText v-model="form.contact_phone" class="w-full" placeholder="手机/座机" />
        </div>
      </div>

      <!-- 审计报告上传 -->
      <div class="border-t pt-4">
        <h3 class="font-bold text-sm mb-2">审计报告文件</h3>
        <div class="flex gap-3 items-center">
          <label class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm cursor-pointer hover:bg-blue-700">
            {{ uploading ? '上传中...' : '上传报告文件' }}
            <input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx" @change="handleFileUpload" :disabled="uploading" class="hidden" />
          </label>
          <span v-if="form.report_file_name" class="text-sm text-green-700 flex gap-2 items-center">
            {{ form.report_file_name }}
            <Button label="下载" icon="pi pi-download" size="small" text severity="info" @click="handleDownload" />
          </span>
          <span v-else class="text-xs text-zinc-400">尚未上传</span>
        </div>
      </div>

      <!-- 三张审定财务报表 -->
      <div class="border-t pt-4">
        <h3 class="font-bold text-sm mb-2">审定财务报表确认</h3>
        <p class="text-xs text-zinc-400 mb-3">勾选表示该报表已经审计机构审定并确认无误</p>
        <div class="flex gap-6">
          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <Checkbox v-model="form.balance_sheet_ok" :binary="true" />
            资产负债表
          </label>
          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <Checkbox v-model="form.income_statement_ok" :binary="true" />
            利润表
          </label>
          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <Checkbox v-model="form.cashflow_statement_ok" :binary="true" />
            现金流量表
          </label>
        </div>
      </div>

      <!-- 备注 -->
      <div class="border-t pt-4">
        <label class="text-xs text-zinc-500 block mb-1">备注</label>
        <Textarea v-model="form.notes" rows="3" class="w-full" placeholder="审计意见摘要、调整事项等..." />
      </div>

      <!-- Save -->
      <div class="border-t pt-4 flex gap-2">
        <Button label="保存" icon="pi pi-check" :loading="saving" @click="handleSave" />
        <span class="text-xs text-zinc-400 self-center">{{ found ? '已保存 · 修改后请再次保存' : '尚未保存' }}</span>
      </div>
    </div>
  </div>
</template>
