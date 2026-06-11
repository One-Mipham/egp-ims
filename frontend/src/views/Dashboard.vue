<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getMe } from '@/api'

const router = useRouter()
const userRole = ref<string>('')

const canViewAccountingCockpit = computed(() =>
  ['accountant', 'finance_manager', 'finance_director', 'super_admin'].includes(userRole.value)
)
const canViewFinanceCockpit = computed(() =>
  ['finance_manager', 'finance_director', 'super_admin'].includes(userRole.value)
)

onMounted(async () => {
  try {
    const me = await getMe()
    userRole.value = me.data.role
  } catch { /* hidden if no role */ }
})
</script>

<template>
  <div class="space-y-8">
    <div class="page-header">
      <h2>管理驾驶舱</h2>
    </div>
    <p class="text-sm text-stone-500 -mt-4">选择以下驾驶舱进入对应管理视图</p>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl">
      <!-- 会计管理驾驶舱入口 -->
      <div
        @click="canViewAccountingCockpit && router.push('/cockpit/accounting')"
        class="border rounded-sm p-6 transition-all shadow-sm hover:shadow-md select-none"
        :class="canViewAccountingCockpit
          ? 'bg-white border-stone-200 cursor-pointer hover:border-emerald-300'
          : 'bg-stone-100 border-stone-200 opacity-60 cursor-not-allowed'"
      >
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-full bg-sky-100 flex items-center justify-center">
            <i class="pi pi-book text-sky-700" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-stone-800">会计管理驾驶舱</h3>
            <p class="text-xs text-stone-500">凭证 · 科目 · 报税 · 对账</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs text-stone-500">
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 凭证统计</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 科目概览</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 报税状态</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 对账状态</span>
        </div>
        <div v-if="!canViewAccountingCockpit" class="mt-3 flex items-center gap-1 text-xs text-stone-400">
          <i class="pi pi-lock text-[10px]" /> 需要会计及以上权限
        </div>
      </div>

      <!-- 财务管理驾驶舱入口 -->
      <div
        @click="canViewFinanceCockpit && router.push('/cockpit/finance')"
        class="border rounded-sm p-6 transition-all shadow-sm hover:shadow-md select-none"
        :class="canViewFinanceCockpit
          ? 'bg-white border-stone-200 cursor-pointer hover:border-amber-300'
          : 'bg-stone-100 border-stone-200 opacity-60 cursor-not-allowed'"
      >
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
            <i class="pi pi-chart-line text-amber-700" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-stone-800">财务管理驾驶舱</h3>
            <p class="text-xs text-stone-500">预算 · 现金流 · 经营指标</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs text-stone-500">
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 预算表现</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 现金流安全</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 偿债/营运/盈利</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 成长能力</span>
        </div>
        <div v-if="!canViewFinanceCockpit" class="mt-3 flex items-center gap-1 text-xs text-stone-400">
          <i class="pi pi-lock text-[10px]" /> 需要财务经理及以上权限
        </div>
      </div>
    </div>
  </div>
</template>
