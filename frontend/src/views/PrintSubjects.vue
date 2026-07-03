<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import { printSubjects } from '@/api'

const subjects = ref<any[]>([])
const loading = ref(false)
const selectedLevel = ref<number | null>(null)
const LEVEL_OPTIONS = [
  { label: '全部科目', value: null },
  { label: '一级科目', value: 1 },
  { label: '二级科目', value: 2 },
  { label: '三级科目', value: 3 },
  { label: '四级科目', value: 4 },
]

async function load() {
  loading.value = true
  try {
    const cid = parseInt(localStorage.getItem('companyId') || '1')
    const res = await printSubjects(cid, selectedLevel.value || undefined)
    subjects.value = res.data
  } catch (e: any) {
    alert(e.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function doPrint() {
  window.print()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center">
        <Dropdown
          v-model="selectedLevel"
          :options="LEVEL_OPTIONS"
          optionLabel="label"
          optionValue="value"
          class="w-40"
          @change="load"
          placeholder="选择级别"
        />
        <Button label="打印" icon="pi pi-print" @click="doPrint" :disabled="!subjects.length" />
      </div>
    </div>

    <p v-if="loading" class="text-zinc-400 text-sm">加载中...</p>

    <div v-if="subjects.length" class="print-area bg-white shadow-sm px-12 pt-8 pb-6 max-w-5xl mx-auto">
      <h1 class="text-2xl font-bold text-center mb-6">科目表</h1>

      <table class="data-table border-collapse border border-stone-300">
        <thead>
          <tr class="border-b-2 border-stone-400 bg-stone-50">
            <th class="text-left py-1.5 px-2 border border-stone-200" style="width: 90px">科目编码</th>
            <th class="text-left py-1.5 px-2 border border-stone-200">科目名称</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="width: 70px">级别</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="width: 80px">科目类别</th>
            <th class="text-center py-1.5 px-2 border border-stone-200" style="width: 70px">余额方向</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in subjects"
            :key="s.code"
            class="border-b border-stone-200"
            :class="{ 'font-bold': s.level === '一级科目' }"
          >
            <td class="py-1.5 px-2 border border-stone-200">{{ s.code }}</td>
            <td class="py-1.5 px-2 border border-stone-200">{{ s.name }}</td>
            <td class="text-center py-1.5 px-2 border border-stone-200">{{ s.level }}</td>
            <td class="text-center py-1.5 px-2 border border-stone-200">{{ s.category }}</td>
            <td class="text-center py-1.5 px-2 border border-stone-200">{{ s.balance_direction }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
@media print {
  @page {
    size: A4 portrait;
    margin: 10mm;
  }
  body * {
    visibility: hidden;
  }
  .print-area,
  .print-area * {
    visibility: visible;
  }
  .print-area {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    margin: 0 auto;
  }
}
</style>
