<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import { printDepartments } from '@/api'

const departments = ref<any[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await printDepartments(cid)
    departments.value = res.data
  } catch (e: any) {
    alert(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function doPrint() { window.print() }

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <Button label="打印" icon="pi pi-print" @click="doPrint" :disabled="!departments.length" />
    </div>

    <p v-if="loading" class="text-zinc-400 text-sm">加载中...</p>

    <div v-if="departments.length" class="print-area bg-white shadow-sm px-12 pt-8 pb-6 max-w-4xl mx-auto">
      <h1 class="text-2xl font-bold text-center mb-6">部门信息表</h1>

      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400 bg-stone-50">
            <th class="text-left py-1.5 px-2 border border-stone-200" style="width:100px">部门编码</th>
            <th class="text-left py-1.5 px-2 border border-stone-200" style="width:180px">部门名称</th>
            <th class="text-left py-1.5 px-2 border border-stone-200" style="width:100px">负责人</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="width:60px">状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in departments" :key="d.code" class="border-b border-stone-200">
            <td class="py-1.5 px-2 border border-stone-200">{{ d.code }}</td>
            <td class="py-1.5 px-2 border border-stone-200">{{ d.name }}</td>
            <td class="py-1.5 px-2 border border-stone-200">{{ d.manager || '-' }}</td>
            <td class="text-center py-1.5 px-2 border border-stone-200">{{ d.is_active ? '启用' : '停用' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
@media print {
  @page { size: A4 portrait; margin: 10mm; }
  body * { visibility: hidden; }
  .print-area, .print-area * { visibility: visible; }
  .print-area { position: absolute; left: 0; top: 0; width: 100%; margin: 0 auto; }
}
</style>
