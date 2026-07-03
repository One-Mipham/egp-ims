<script setup lang="ts">
import Card from 'primevue/card'

const sections = [
  {
    num: '1',
    label: '公共资料',
    icon: 'pi pi-folder-open',
    desc: '修改基本信息、会计期间、用户权限',
    items: [
      { label: '基本信息', to: '/settings/basic' },
      { label: '会计期间', to: '/periods' },
      { label: '用户权限', to: '/permissions' },
    ],
  },
  {
    num: '2',
    label: '选项设置',
    icon: 'pi pi-sliders-h',
    desc: '配置业务流程参数与系统偏好',
    items: [{ label: '进入选项设置', to: '/settings/options' }],
  },
  {
    num: '3',
    label: '基础档案',
    icon: 'pi pi-bookmark',
    desc: '导入或录入业务合同、发票等历史档案',
    items: [
      { label: '业务合同', to: '/init/contracts' },
      { label: '业务发票', to: '/init/invoices' },
      { label: '历史年度记账凭证', to: '/init/voucher-archive' },
      { label: '会计月报表', to: '/init/monthly-reports' },
      { label: '年度审计报表', to: '/init/annual-audit' },
    ],
  },
  {
    num: '4',
    label: '单据设置',
    icon: 'pi pi-file',
    desc: '配置凭证类别与单据模板',
    items: [{ label: '进入单据设置', to: '/settings/voucher-types' }],
  },
  {
    num: '5',
    label: '期初数据',
    icon: 'pi pi-sync',
    desc: '录入或导入科目期初余额',
    items: [{ label: '进入期初数据', to: '/init/opening-balances' }],
  },
]
</script>

<template>
  <div>
    <h1 class="text-xl font-light text-zinc-800 mb-1 tracking-tight">初始化导航</h1>
    <p class="text-sm text-zinc-500 mb-6 leading-relaxed">
      用户可以进入公共资料修改基本信息、会计期间、业务流程或设置用户、用户组一级赋予相应功能、字段和数据权限
    </p>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card v-for="s in sections" :key="s.num" class="shadow-sm border border-zinc-200">
        <template #title>
          <div class="flex items-center gap-3">
            <span
              class="w-7 h-7 rounded-full bg-emerald-700 text-white text-xs flex items-center justify-center font-medium shrink-0"
            >
              {{ s.num }}
            </span>
            <span class="text-base font-medium text-zinc-800">{{ s.label }}</span>
          </div>
        </template>
        <template #content>
          <p class="text-xs text-zinc-500 mb-3">{{ s.desc }}</p>
          <div class="flex flex-wrap gap-2">
            <router-link
              v-for="item in s.items"
              :key="item.to"
              :to="item.to"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors"
            >
              <i :class="s.icon" style="font-size: 11px" />
              {{ item.label }}
            </router-link>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>
