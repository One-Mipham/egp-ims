<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import { getYearlySummary } from '@/api'
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const year = ref(new Date().getFullYear())
const summary = ref<any>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getYearlySummary(companyId.value, year.value)
    summary.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">年度结账</h2>
      <div class="flex gap-2 items-center">
        <Button
          icon="pi pi-chevron-left"
          text
          rounded
          @click="year--; load()"
        />
        <span class="text-xl font-bold text-zinc-700 w-20 text-center">{{ year }}</span>
        <Button
          icon="pi pi-chevron-right"
          text
          rounded
          @click="year++; load()"
        />
      </div>
    </div>

    <div v-if="summary" class="grid grid-cols-4 gap-3 mb-4">
      <div class="bg-white rounded-sm border border-stone-200 p-4 text-center">
        <div class="text-sm text-zinc-500">年度状态</div>
        <Tag
          :value="summary.is_year_closed ? '已年结' : '未年结'"
          :severity="summary.is_year_closed ? 'success' : 'warning'"
          class="mt-2"
        />
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4 text-center">
        <div class="text-sm text-zinc-500">已关账月</div>
        <div class="text-2xl font-bold text-green-600 mt-1">{{ summary.closed_months }}</div>
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4 text-center">
        <div class="text-sm text-zinc-500">未关账月</div>
        <div class="text-2xl font-bold text-red-600 mt-1">{{ summary.total_months - summary.closed_months }}</div>
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4 text-center">
        <div class="text-sm text-zinc-500">总月份</div>
        <div class="text-2xl font-bold text-zinc-700 mt-1">{{ summary.total_months }}</div>
      </div>
    </div>

    <div class="grid grid-cols-6 gap-2">
      <div
        v-for="m in summary?.months"
        :key="m.period"
        class="bg-white rounded-sm border p-3 text-center"
        :class="m.is_closed ? 'border-green-300' : 'border-stone-200'"
      >
        <div class="text-sm font-bold text-zinc-700">{{ m.period }}</div>
        <Tag
          :value="m.is_closed ? '已关' : '未关'"
          :severity="m.is_closed ? 'success' : 'warning'"
          class="mt-1 text-xs"
        />
      </div>
    </div>
  </div>
</template>
