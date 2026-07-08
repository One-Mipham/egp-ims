<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import { getQuarterlySummary } from '@/api'
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))
const year = ref(new Date().getFullYear())
const quarters = ref<any[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getQuarterlySummary(companyId.value, year.value)
    quarters.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">季度结账</h2>
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

    <div class="grid grid-cols-4 gap-4">
      <div
        v-for="q in quarters"
        :key="q.quarter"
        class="bg-white rounded-sm border p-6 flex flex-col gap-3"
        :class="q.is_quarter_closed ? 'border-green-300' : 'border-stone-200'"
      >
        <div class="flex justify-between items-center">
          <span class="text-xl font-bold text-zinc-700">{{ q.quarter }}</span>
          <Tag
            :value="q.is_quarter_closed ? '已完成' : `${q.closed_months}/${q.total_months}`"
            :severity="q.is_quarter_closed ? 'success' : q.closed_months > 0 ? 'info' : 'warning'"
          />
        </div>
        <div class="flex gap-2 text-sm text-zinc-500">
          <span v-for="m in q.months" :key="m" class="bg-stone-50 rounded px-2 py-1">{{ m }}</span>
        </div>
        <div class="text-sm text-zinc-500">
          已关账月份：<strong>{{ q.closed_months }}</strong> / {{ q.total_months }}
        </div>
        <div class="w-full bg-stone-200 rounded-full h-2">
          <div
            class="h-2 rounded-full transition-all"
            :class="q.is_quarter_closed ? 'bg-green-500 w-full' : 'bg-blue-400'"
            :style="{ width: (q.closed_months / q.total_months) * 100 + '%' }"
          />
        </div>
      </div>
    </div>
  </div>
</template>
