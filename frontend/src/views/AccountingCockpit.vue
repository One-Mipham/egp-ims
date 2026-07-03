<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listVouchers, listPeriods, listAccounts, listDepartments } from '@/api'

const stats = ref([
  { label: '凭证总数', value: 0, icon: 'pi pi-file', circleClass: 'circle-sky' },
  { label: '科目数量', value: 0, icon: 'pi pi-book', circleClass: 'circle-indigo' },
  { label: '部门数量', value: 0, icon: 'pi pi-building', circleClass: 'circle-emerald' },
  { label: '已结账期间', value: 0, icon: 'pi pi-check-circle', circleClass: 'circle-violet' },
])

const taxFiledOnTime = ref<boolean | null>(null)
const bankReconciled = ref<boolean | null>(null)
const loading = ref(false)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

onMounted(async () => {
  loading.value = true
  try {
    const [v, a, d, p] = await Promise.all([
      listVouchers(companyId.value),
      listAccounts(companyId.value),
      listDepartments(companyId.value),
      listPeriods(companyId.value),
    ])
    stats.value[0].value = v.data.length
    stats.value[1].value = a.data.length
    stats.value[2].value = d.data.length
    stats.value[3].value = p.data.filter((x: any) => x.is_closed).length
  } catch {
    /* use defaults */
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <div class="page-header">
      <h2>会计管理驾驶舱</h2>
    </div>

    <div class="flex flex-wrap gap-6 justify-start">
      <div v-for="stat in stats" :key="stat.label" :class="['cockpit-circle', stat.circleClass]">
        <div class="circle-ring" />
        <i :class="['pi', stat.icon, 'circle-icon']" :style="{ color: 'var(--color-text-secondary)' }" />
        <div class="circle-value">{{ stat.value }}</div>
        <div class="circle-label">{{ stat.label }}</div>
      </div>

      <div
        :class="[
          'cockpit-circle cursor-pointer',
          taxFiledOnTime === true ? 'circle-green' : taxFiledOnTime === false ? 'circle-red' : 'circle-zinc',
        ]"
        @click="taxFiledOnTime = taxFiledOnTime === null ? true : taxFiledOnTime === true ? false : null"
      >
        <div class="circle-ring" />
        <i
          :class="[
            'pi',
            taxFiledOnTime === true ? 'pi-check-circle' : taxFiledOnTime === false ? 'pi-times-circle' : 'pi-calendar',
            'circle-icon',
          ]"
          :style="{
            color:
              taxFiledOnTime === true
                ? '#059669'
                : taxFiledOnTime === false
                  ? '#dc2626'
                  : 'var(--color-text-secondary)',
          }"
        />
        <div class="text-xs font-medium mt-1">
          {{ taxFiledOnTime === true ? '已报税' : taxFiledOnTime === false ? '未报税' : '点击设置' }}
        </div>
        <div class="circle-label">按时报税</div>
      </div>

      <div
        :class="[
          'cockpit-circle cursor-pointer',
          bankReconciled === true ? 'circle-green' : bankReconciled === false ? 'circle-red' : 'circle-zinc',
        ]"
        @click="bankReconciled = bankReconciled === null ? true : bankReconciled === true ? false : null"
      >
        <div class="circle-ring" />
        <i
          :class="[
            'pi',
            bankReconciled === true ? 'pi-check-circle' : bankReconciled === false ? 'pi-times-circle' : 'pi-building',
            'circle-icon',
          ]"
          :style="{
            color:
              bankReconciled === true
                ? '#059669'
                : bankReconciled === false
                  ? '#dc2626'
                  : 'var(--color-text-secondary)',
          }"
        />
        <div class="text-xs font-medium mt-1">
          {{ bankReconciled === true ? '已对账' : bankReconciled === false ? '未对账' : '点击设置' }}
        </div>
        <div class="circle-label">银行对账</div>
      </div>
    </div>

    <p v-if="loading" class="text-stone-400 text-xs tracking-wide">加载数据中...</p>
  </div>
</template>
