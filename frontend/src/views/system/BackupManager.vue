<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import api from '@/api'
import { listBackups, createBackup } from '@/api'

const props = defineProps<{ type: 'monthly' | 'yearly'; title: string }>()

const backups = ref<any[]>([])
const loading = ref(false)
const actionLoading = ref(false)
const _label = ref('')
const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)

const typeLabel = props.type === 'yearly' ? '年度' : '月度'

async function fetchBackups() {
  loading.value = true
  try {
    const res = await listBackups(props.type)
    backups.value = res.data || []
  } catch {
    backups.value = []
  } finally {
    loading.value = false
  }
}

async function doBackup() {
  actionLoading.value = true
  try {
    const lbl = props.type === 'yearly' ? `${year.value}` : `${year.value}-${String(month.value).padStart(2, '0')}`
    await createBackup(props.type, lbl)
    await fetchBackups()
  } catch (e: any) {
    alert(e.response?.data?.detail || '备份失败')
  } finally {
    actionLoading.value = false
  }
}

function _downloadUrl(filename: string) {
  const base = (window as any).__API_BASE__ || ''
  const cid = localStorage.getItem('companyId') || '1'
  return `${base}/api/system/backups/${filename}?type=${props.type}&company_id=${cid}`
}

function doDownload(filename: string) {
  const token = localStorage.getItem('token')
  const base = (window as any).__API_BASE__ || ''
  const cid = localStorage.getItem('companyId') || '1'
  const url = `${base}/api/system/backups/${filename}?type=${props.type}&company_id=${cid}`
  // Create a temporary link with auth header
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  // Use fetch with auth for the actual download
  fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => r.blob())
    .then(blob => {
      const blobUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename
      a.click()
      URL.revokeObjectURL(blobUrl)
    })
}

async function doDelete(filename: string) {
  if (!confirm(`确定删除备份 "${filename}"？`)) return
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    await api.delete(`/system/backups/${filename}?type=${props.type}&company_id=${cid}`)
    await fetchBackups()
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function _dateFromFilename(fn: string) {
  const m = fn.match(/(\d{8})_(\d{6})/)
  if (m) return `${m[1].slice(0, 4)}-${m[1].slice(4, 6)}-${m[1].slice(6, 8)} ${m[2].slice(0, 2)}:${m[2].slice(2, 4)}`
  return fn
}

onMounted(fetchBackups)
</script>

<template>
  <div class="max-w-3xl">
    <h2 class="text-lg font-bold mb-4">{{ title }}</h2>

    <!-- Create backup -->
    <div class="bg-white border rounded p-4 mb-4">
      <h3 class="font-bold text-sm mb-3">创建{{ typeLabel }}备份</h3>
      <div class="flex gap-2 items-end flex-wrap">
        <div v-if="type === 'yearly'" class="flex flex-col gap-1">
          <label class="text-xs text-zinc-500">年度</label>
          <input v-model.number="year" type="number" class="border rounded px-2 py-1.5 text-sm w-28" />
        </div>
        <template v-else>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-zinc-500">年</label>
            <input v-model.number="year" type="number" class="border rounded px-2 py-1.5 text-sm w-24" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-zinc-500">月</label>
            <select v-model.number="month" class="border rounded px-2 py-1.5 text-sm w-20">
              <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
            </select>
          </div>
        </template>
        <Button label="创建备份" icon="pi pi-save" @click="doBackup" :loading="actionLoading" size="small" />
      </div>
      <p class="text-xs text-zinc-400 mt-2">备份将复制当前数据库文件到服务器备份目录。</p>
    </div>

    <!-- Backup list -->
    <div class="bg-white border rounded p-4">
      <h3 class="font-bold text-sm mb-3">已有备份 ({{ backups.length }})</h3>
      <p v-if="loading" class="text-xs text-zinc-400">加载中...</p>
      <p v-if="!loading && !backups.length" class="text-xs text-zinc-400">暂无备份</p>
      <div v-if="backups.length" class="overflow-x-auto">
        <table class="w-full text-sm border-collapse">
          <thead>
            <tr class="border-b text-left text-xs text-zinc-500">
              <th class="py-2">文件名</th>
              <th class="py-2">大小</th>
              <th class="py-2">创建时间</th>
              <th class="py-2">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in backups" :key="b.filename" class="border-b last:border-b-0">
              <td class="py-2 font-mono text-xs">{{ b.filename }}</td>
              <td class="py-2">{{ b.size_kb }} KB</td>
              <td class="py-2 text-xs text-zinc-500">{{ b.created_at }}</td>
              <td class="py-2">
                <div class="flex gap-1">
                  <button @click="doDownload(b.filename)" class="text-blue-600 hover:text-blue-800 text-xs">下载</button>
                  <button @click="doDelete(b.filename)" class="text-red-500 hover:text-red-700 text-xs ml-2">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
